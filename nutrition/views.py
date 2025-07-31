# nutrition/views.py
from rest_framework import generics, filters, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Count, Sum
from django_filters.rest_framework import DjangoFilterBackend
from .models import Food, FoodCategory
from .serializers import (
    FoodListSerializer, FoodDetailSerializer, FoodSearchSerializer,
    FoodCategorySerializer
)
from .services import USDAFoodDataService

class StandardResultsSetPagination(PageNumberPagination):
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100

class FoodCategoryListView(generics.ListAPIView):
    """Lista todas las categorías de alimentos"""
    queryset = FoodCategory.objects.all()
    serializer_class = FoodCategorySerializer
    permission_classes = []  # Público

class FoodListView(generics.ListAPIView):
    """Lista alimentos con filtros y búsqueda"""
    queryset = Food.objects.select_related('category').all()
    serializer_class = FoodListSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    permission_classes = []  # Público
    
    # Campos de búsqueda
    search_fields = ['name', 'name_es', 'aliases__alias']
    
    # Campos de ordenamiento
    ordering_fields = ['name', 'calories', 'protein', 'protein_density']
    ordering = ['name']
    
    # Filtros
    filterset_fields = {
        'category': ['exact'],
        'calories': ['gte', 'lte'],
        'protein': ['gte', 'lte'],
        'carbohydrate': ['gte', 'lte'],
        'fat': ['gte', 'lte'],
        'fiber': ['gte', 'lte'],
        'sodium': ['gte', 'lte'],
        'is_verified': ['exact'],
    }
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filtros personalizados
        high_protein = self.request.query_params.get('high_protein')
        if high_protein == 'true':
            queryset = queryset.filter(protein__gte=15)
        
        low_carb = self.request.query_params.get('low_carb')
        if low_carb == 'true':
            queryset = queryset.filter(carbohydrate__lte=10)
        
        high_fiber = self.request.query_params.get('high_fiber')
        if high_fiber == 'true':
            queryset = queryset.filter(fiber__gte=5)
        
        low_sodium = self.request.query_params.get('low_sodium')
        if low_sodium == 'true':
            queryset = queryset.filter(sodium__lte=140)
        
        return queryset

class FoodDetailView(generics.RetrieveAPIView):
    """Detalle completo de un alimento"""
    queryset = Food.objects.select_related('category').prefetch_related('aliases')
    serializer_class = FoodDetailSerializer
    permission_classes = []  # Público

class FoodSearchView(generics.ListAPIView):
    """Búsqueda optimizada de alimentos"""
    serializer_class = FoodSearchSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = []  # Público
    
    def get_queryset(self):
        query = self.request.query_params.get('q', '')
        if not query:
            return Food.objects.none()
        
        # Búsqueda en múltiples campos
        return Food.objects.select_related('category').filter(
            Q(name__icontains=query) |
            Q(name_es__icontains=query) |
            Q(aliases__alias__icontains=query)
        ).distinct()

@api_view(['GET'])
def food_suggestions(request):
    """Sugerencias de alimentos para autocompletado"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return Response([])
    
    foods = Food.objects.filter(
        Q(name__icontains=query) | Q(name_es__icontains=query)
    )[:10]
    
    suggestions = []
    for food in foods:
        suggestions.append({
            'id': food.id,
            'name': food.name_es or food.name,
            'category': food.category.name_es if food.category else 'Sin categoría',
            'calories': food.calories,
            'protein': food.protein
        })
    
    return Response(suggestions)

@api_view(['GET'])
def nutrition_analysis(request):
    """Análisis nutricional de múltiples alimentos"""
    food_ids = request.GET.get('food_ids', '').split(',')
    quantities = request.GET.get('quantities', '').split(',')
    
    if len(food_ids) != len(quantities):
        return Response(
            {'error': 'Número de alimentos y cantidades debe coincidir'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    total_nutrition = {
        'calories': 0, 'protein': 0, 'carbohydrate': 0, 'fat': 0,
        'fiber': 0, 'sodium': 0, 'calcium': 0, 'iron': 0
    }
    
    foods_analysis = []
    
    try:
        for food_id, quantity in zip(food_ids, quantities):
            if not food_id or not quantity:
                continue
                
            food = Food.objects.get(id=int(food_id))
            qty = float(quantity)
            factor = qty / food.serving_size
            
            food_nutrition = {
                'food_id': food.id,
                'food_name': food.name_es or food.name,
                'quantity': qty,
                'calories': round(food.calories * factor, 1),
                'protein': round(food.protein * factor, 1),
                'carbohydrate': round(food.carbohydrate * factor, 1),
                'fat': round(food.fat * factor, 1),
                'fiber': round(food.fiber * factor, 1),
                'sodium': round(food.sodium * factor, 1),
            }
            
            foods_analysis.append(food_nutrition)
            
            # Sumar al total
            for nutrient in total_nutrition:
                if nutrient in food_nutrition:
                    total_nutrition[nutrient] += food_nutrition[nutrient]
        
        # Redondear totales
        for nutrient in total_nutrition:
            total_nutrition[nutrient] = round(total_nutrition[nutrient], 1)
        
        return Response({
            'total_nutrition': total_nutrition,
            'foods_breakdown': foods_analysis,
            'food_count': len(foods_analysis)
        })
        
    except (ValueError, Food.DoesNotExist) as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )

@api_view(['GET'])
def similar_foods(request, food_id):
    """Encuentra alimentos similares nutricionalmente"""
    try:
        food = Food.objects.get(id=food_id)
        
        # Buscar alimentos similares basados en macronutrientes
        similar = Food.objects.filter(
            calories__range=(food.calories * 0.8, food.calories * 1.2),
            protein__range=(food.protein * 0.7, food.protein * 1.3)
        ).exclude(id=food_id)[:10]
        
        serializer = FoodListSerializer(similar, many=True)
        return Response({
            'reference_food': FoodDetailSerializer(food).data,
            'similar_foods': serializer.data
        })
        
    except Food.DoesNotExist:
        return Response(
            {'error': 'Alimento no encontrado'}, 
            status=status.HTTP_404_NOT_FOUND
        )

## API usda
@api_view(['GET'])
def search_usda_foods(request):
    """Buscar alimentos en USDA API"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return Response({'error': 'Query muy corto'}, status=status.HTTP_400_BAD_REQUEST)
    
    usda_service = USDAFoodDataService()
    results = usda_service.search_foods(query, max_results=10)
    
    if 'error' in results:
        return Response(results, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Formatear resultados para el frontend
    formatted_results = []
    for food in results.get('foods', []):
        formatted_results.append({
            'fdc_id': food.get('fdcId'),
            'description': food.get('description'),
            'brand_owner': food.get('brandOwner', ''),
            'food_category': food.get('foodCategory', 'Sin categoría'),
            'data_type': food.get('dataType'),
            'score': food.get('score', 0)
        })
    
    return Response({
        'results': formatted_results,
        'total': results.get('totalHits', 0),
        'source': 'USDA FoodData Central'
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def import_usda_food(request):
    """Importar un alimento desde USDA a nuestra BD"""
    fdc_id = request.data.get('fdc_id')
    if not fdc_id:
        return Response({'error': 'FDC ID requerido'}, status=status.HTTP_400_BAD_REQUEST)
    
    usda_service = USDAFoodDataService()
    result = usda_service.import_food_from_usda(fdc_id)
    
    if 'error' in result:
        return Response(result, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    # Serializar el alimento importado
    from .serializers import FoodDetailSerializer
    food_data = FoodDetailSerializer(result['food']).data
    
    return Response({
        'message': result['message'],
        'food': food_data,
        'created': result['created']
    })

@api_view(['GET'])
def enhanced_food_search(request):
    """Búsqueda combinada: local + USDA"""
    query = request.GET.get('q', '')
    if len(query) < 2:
        return Response({'error': 'Query muy corto'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Buscar primero en BD local
    local_foods = Food.objects.filter(
        Q(name__icontains=query) | Q(name_es__icontains=query)
    )[:5]
    
    local_results = FoodSearchSerializer(local_foods, many=True).data
    
    # Buscar en USDA si hay pocos resultados locales
    usda_results = []
    if len(local_results) < 3:
        usda_service = USDAFoodDataService()
        usda_data = usda_service.search_foods(query, max_results=5)
        
        if 'foods' in usda_data:
            for food in usda_data['foods']:
                usda_results.append({
                    'fdc_id': food.get('fdcId'),
                    'name': food.get('description'),
                    'source': 'USDA',
                    'brand': food.get('brandOwner', ''),
                    'category': food.get('foodCategory', 'Sin categoría')
                })
    
    return Response({
        'local_results': local_results,
        'usda_results': usda_results,
        'combined_count': len(local_results) + len(usda_results)
    })