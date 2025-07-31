# recommendations/views.py
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from .models import (
    UserFoodRating, NutritionalProfile, DailyNutritionLog,
    FoodConsumption, RecommendationSession, Recommendation
)
from .serializers import (
    UserFoodRatingSerializer, NutritionalProfileSerializer,
    DailyNutritionLogSerializer, FoodConsumptionSerializer,
    RecommendationSessionSerializer
)
from .engine import RecommendationEngine
from nutrition.models import Food

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_recommendations(request):
    """Obtener recomendaciones personalizadas"""
    user = request.user
    
    # Verificar que el usuario tenga perfil completo
    if not user.profile_completed:
        return Response({
            'error': 'Perfil incompleto. Complete su información personal primero.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # NUEVO: Asegurar que existe perfil nutricional
    nutritional_profile, created = NutritionalProfile.objects.get_or_create(
        user=user,
        defaults={
            'target_calories': user.daily_calories or 2000,
            'target_protein': user.daily_protein or 150,
            'target_carbs': user.daily_carbs or 250,
            'target_fat': user.daily_fat or 65,
            'target_fiber': 25,
            'max_sodium': 2300,
            'min_calcium': 1000,
            'min_iron': 8,
            'min_vitamin_c': 90
        }
    )
    
    # Parámetros de la solicitud
    session_type = request.data.get('session_type', 'meal_suggestion')
    meal_type = request.data.get('meal_type')  # breakfast, lunch, dinner, snack
    count = min(request.data.get('count', 10), 20)  # Máximo 20
    
    # Obtener estado nutricional actual del día
    today = timezone.now().date()
    daily_log, created = DailyNutritionLog.objects.get_or_create(
        user=user, date=today
    )
    
    current_nutrition = {
        'calories': daily_log.consumed_calories,
        'protein': daily_log.consumed_protein,
        'carbs': daily_log.consumed_carbs,
        'fat': daily_log.consumed_fat,
        'fiber': daily_log.consumed_fiber,
        'sodium': daily_log.consumed_sodium
    }
    
    # Inicializar motor de recomendaciones
    engine = RecommendationEngine(user)
    
    try:
        # Obtener recomendaciones
        recommendations_data = engine.get_recommendations(
            session_type=session_type,
            meal_type=meal_type,
            current_nutrition=current_nutrition,
            count=count
        )
        
        # Crear sesión de recomendación
        session = RecommendationSession.objects.create(
            user=user,
            session_type=session_type,
            current_nutrition=current_nutrition,
            user_preferences=request.data
        )
        
        # Crear registros de recomendación
        recommendations = []
        for i, rec_data in enumerate(recommendations_data):
            recommendation = Recommendation.objects.create(
                session=session,
                food=rec_data['food'],
                total_score=rec_data['total_score'],
                nutrition_score=rec_data['nutrition_score'],
                preference_score=rec_data['preference_score'],
                variety_score=rec_data['variety_score'],
                suggested_quantity=rec_data['suggested_quantity'],
                reason=rec_data['reason'],
                position=i + 1
            )
            recommendations.append(recommendation)
        
        # Serializar respuesta
        session_serializer = RecommendationSessionSerializer(session)
        
        return Response({
            'session': session_serializer.data,
            'current_nutrition': current_nutrition,
            'nutrition_targets': {
                'calories': user.daily_calories,
                'protein': user.daily_protein,
                'carbs': user.daily_carbs,
                'fat': user.daily_fat
            },
            'remaining_nutrition': {
                'calories': max(0, user.daily_calories - daily_log.consumed_calories),
                'protein': max(0, user.daily_protein - daily_log.consumed_protein),
                'carbs': max(0, user.daily_carbs - daily_log.consumed_carbs),
                'fat': max(0, user.daily_fat - daily_log.consumed_fat)
            }
        })
        
    except Exception as e:
        return Response({
            'error': f'Error generando recomendaciones: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def log_food_consumption(request):
    """Registrar consumo de alimento"""
    user = request.user
    
    try:
        food_id = request.data.get('food_id')
        quantity = float(request.data.get('quantity'))
        meal_type = request.data.get('meal_type')
        
        food = Food.objects.get(id=food_id)
        
        # Obtener o crear log diario
        today = timezone.now().date()
        daily_log, created = DailyNutritionLog.objects.get_or_create(
            user=user, date=today
        )
        
        # NUEVO: Asegurar que existe perfil nutricional
        nutritional_profile, profile_created = NutritionalProfile.objects.get_or_create(
            user=user,
            defaults={
                'target_calories': user.daily_calories or 2000,
                'target_protein': user.daily_protein or 150,
                'target_carbs': user.daily_carbs or 250,
                'target_fat': user.daily_fat or 65,
                'target_fiber': 25,
                'max_sodium': 2300,
                'min_calcium': 1000,
                'min_iron': 8,
                'min_vitamin_c': 90
            }
        )
        
        with transaction.atomic():
            # Crear registro de consumo
            consumption = FoodConsumption.objects.create(
                daily_log=daily_log,
                food=food,
                quantity=quantity,
                meal_type=meal_type
            )
            
            # Actualizar totales del día
            daily_log.consumed_calories += consumption.calories_consumed
            daily_log.consumed_protein += consumption.protein_consumed
            daily_log.consumed_carbs += consumption.carbs_consumed
            daily_log.consumed_fat += consumption.fat_consumed
            
            # Calcular fibra y sodio proporcionalmente
            factor = quantity / food.serving_size
            daily_log.consumed_fiber += food.fiber * factor
            daily_log.consumed_sodium += food.sodium * factor
            
            # Recalcular scores
            daily_log.adherence_score = daily_log.calculate_adherence_score()
            daily_log.save()
            
            # Aprender de este consumo para futuras recomendaciones
            engine = RecommendationEngine(user)
            engine.learn_from_consumption(consumption)
        
        return Response({
            'message': 'Consumo registrado exitosamente',
            'consumption': FoodConsumptionSerializer(consumption).data,
            'daily_totals': {
                'calories': round(daily_log.consumed_calories, 1),
                'protein': round(daily_log.consumed_protein, 1),
                'carbs': round(daily_log.consumed_carbs, 1),
                'fat': round(daily_log.consumed_fat, 1),
                'adherence_score': daily_log.adherence_score
            }
        })
        
    except Food.DoesNotExist:
        return Response({'error': 'Alimento no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    except (ValueError, KeyError) as e:
        return Response({'error': f'Datos inválidos: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': f'Error interno: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def rate_food(request):
    """Calificar un alimento"""
    user = request.user
    
    try:
        food_id = request.data.get('food_id')
        rating = int(request.data.get('rating'))
        notes = request.data.get('notes', '')
        meal_type = request.data.get('meal_type')
        
        if not 1 <= rating <= 5:
            return Response({'error': 'Rating debe estar entre 1 y 5'}, status=status.HTTP_400_BAD_REQUEST)
        
        food = Food.objects.get(id=food_id)
        
        # Crear o actualizar calificación
        food_rating, created = UserFoodRating.objects.update_or_create(
            user=user,
            food=food,
            defaults={
                'rating': rating,
                'notes': notes,
                'meal_type': meal_type
            }
        )
        
        action = 'creada' if created else 'actualizada'
        return Response({
            'message': f'Calificación {action} exitosamente',
            'rating': UserFoodRatingSerializer(food_rating).data
        })
        
    except Food.DoesNotExist:
        return Response({'error': 'Alimento no encontrado'}, status=status.HTTP_404_NOT_FOUND)
    except (ValueError, KeyError) as e:
        return Response({'error': f'Datos inválidos: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def daily_nutrition_summary(request):
    """Resumen nutricional del día"""
    user = request.user
    date_str = request.GET.get('date', timezone.now().date().isoformat())
    
    try:
        date = timezone.datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        daily_log = DailyNutritionLog.objects.get(user=user, date=date)
        serializer = DailyNutritionLogSerializer(daily_log)
        
        # Obtener objetivos del usuario
        targets = {
            'calories': user.daily_calories or 2000,
            'protein': user.daily_protein or 150,
            'carbs': user.daily_carbs or 250,
            'fat': user.daily_fat or 65
        }
        
        # Calcular porcentajes de cumplimiento
        percentages = {}
        for nutrient, target in targets.items():
            consumed = getattr(daily_log, f'consumed_{nutrient}')
            percentages[nutrient] = round((consumed / target) * 100, 1) if target > 0 else 0
        
        return Response({
            'daily_log': serializer.data,
            'targets': targets,
            'percentages': percentages,
            'is_today': date == timezone.now().date()
        })
        
    except DailyNutritionLog.DoesNotExist:
        return Response({
            'message': 'No hay registros para esta fecha',
            'targets': {
                'calories': user.daily_calories or 2000,
                'protein': user.daily_protein or 150,
                'carbs': user.daily_carbs or 250,
                'fat': user.daily_fat or 65
            },
            'consumed': {
                'calories': 0, 'protein': 0, 'carbs': 0, 'fat': 0
            }
        })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def recommendation_feedback(request):
    """Registrar feedback sobre una recomendación"""
    user = request.user
    
    try:
        recommendation_id = request.data.get('recommendation_id')
        feedback = request.data.get('feedback')  # 'accepted', 'rejected', 'modified'
        
        if feedback not in ['accepted', 'rejected', 'modified']:
            return Response({'error': 'Feedback inválido'}, status=status.HTTP_400_BAD_REQUEST)
        
        recommendation = Recommendation.objects.get(
            id=recommendation_id,
            session__user=user
        )
        
        recommendation.user_feedback = feedback
        recommendation.save()
        
        # Si fue rechazado, aprender de ello
        if feedback == 'rejected':
            engine = RecommendationEngine(user)
            # Reducir preferencia por este alimento
            from .models import UserFoodPreference
            preference, created = UserFoodPreference.objects.get_or_create(
                user=user,
                food=recommendation.food,
                defaults={'preference_score': -0.1, 'confidence': 0.5}
            )
            if not created:
                preference.preference_score = max(-1.0, preference.preference_score - 0.1)
                preference.save()
        
        return Response({'message': 'Feedback registrado exitosamente'})
        
    except Recommendation.DoesNotExist:
        return Response({'error': 'Recomendación no encontrada'}, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_nutrition_insights(request):
    """Insights y análisis del comportamiento nutricional del usuario"""
    user = request.user
    days = int(request.GET.get('days', 7))  # Análisis de últimos N días
    
    from django.utils import timezone
    from datetime import timedelta
    
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=days-1)
    
    daily_logs = DailyNutritionLog.objects.filter(
        user=user,
        date__range=[start_date, end_date]
    ).order_by('date')
    
    if not daily_logs.exists():
        return Response({
            'message': 'No hay suficientes datos para generar insights'
        })
    
    # Calcular promedios
    avg_calories = sum(log.consumed_calories for log in daily_logs) / len(daily_logs)
    avg_protein = sum(log.consumed_protein for log in daily_logs) / len(daily_logs)
    avg_adherence = sum(log.adherence_score or 0 for log in daily_logs) / len(daily_logs)
    
    # Identificar patrones
    patterns = {
        'consistent_days': len([log for log in daily_logs if log.adherence_score and log.adherence_score >= 70]),
        'high_protein_days': len([log for log in daily_logs if log.consumed_protein >= user.daily_protein * 0.8]),
        'balanced_days': len([log for log in daily_logs if log.balance_score and log.balance_score >= 70])
    }
    
    # Obtener comidas más frecuentes
    from django.db.models import Count
    frequent_foods = FoodConsumption.objects.filter(
        daily_log__user=user,
        daily_log__date__range=[start_date, end_date]
    ).values('food__name_es', 'food__name').annotate(
        count=Count('food')
    ).order_by('-count')[:5]
    
    # Recomendaciones de mejora
    recommendations_for_improvement = []
    
    if avg_protein < user.daily_protein * 0.8:
        recommendations_for_improvement.append({
            'area': 'Proteína',
            'message': 'Considera aumentar tu consumo de proteína',
            'suggestion': 'Incluye más carnes magras, huevos, o legumbres'
        })
    
    if avg_adherence < 60:
        recommendations_for_improvement.append({
            'area': 'Consistencia',
            'message': 'Trabaja en ser más consistente con tus objetivos',
            'suggestion': 'Planifica tus comidas con anticipación'
        })
    
    return Response({
        'period': f'Últimos {days} días',
        'averages': {
            'calories': round(avg_calories, 1),
            'protein': round(avg_protein, 1),
            'adherence_score': round(avg_adherence, 1)
        },
        'patterns': patterns,
        'frequent_foods': list(frequent_foods),
        'improvement_recommendations': recommendations_for_improvement,
        'daily_data': [
            {
                'date': log.date.isoformat(),
                'calories': log.consumed_calories,
                'protein': log.consumed_protein,
                'adherence': log.adherence_score
            } for log in daily_logs
        ]
    })

class NutritionalProfileView(generics.RetrieveUpdateAPIView):
    """Ver y actualizar perfil nutricional"""
    serializer_class = NutritionalProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        profile, created = NutritionalProfile.objects.get_or_create(
            user=self.request.user,
            defaults={
                'target_calories': self.request.user.daily_calories or 2000,
                'target_protein': self.request.user.daily_protein or 150,
                'target_carbs': self.request.user.daily_carbs or 250,
                'target_fat': self.request.user.daily_fat or 65
            }
        )
        return profile

class UserFoodRatingListView(generics.ListCreateAPIView):
    """Lista y crear calificaciones de alimentos"""
    serializer_class = UserFoodRatingSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserFoodRating.objects.filter(user=self.request.user).order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def get_simple_recommendations(request):
    """Recomendaciones simples - versión de emergencia"""
    user = request.user
    
    # Parámetros
    meal_type = request.data.get('meal_type')
    count = min(request.data.get('count', 5), 10)
    
    try:
        from nutrition.models import Food
        from django.db.models import Q
        import random
        
        # Obtener alimentos básicos sin filtros complejos
        foods = Food.objects.all()
        
        # Filtro simple por tipo de comida
        if meal_type == 'breakfast':
            # Buscar alimentos típicos de desayuno
            breakfast_keywords = ['egg', 'milk', 'bread', 'fruit', 'yogurt', 'oat', 'cereal', 'banana', 'apple']
            breakfast_q = Q()
            for keyword in breakfast_keywords:
                breakfast_q |= Q(name__icontains=keyword)
            
            breakfast_foods = foods.filter(breakfast_q)
            if breakfast_foods.exists():
                foods = breakfast_foods
        
        elif meal_type == 'lunch' or meal_type == 'dinner':
            # Alimentos más sustanciosos
            main_keywords = ['chicken', 'rice', 'beef', 'fish', 'pasta', 'potato', 'beans']
            main_q = Q()
            for keyword in main_keywords:
                main_q |= Q(name__icontains=keyword)
            
            main_foods = foods.filter(main_q)
            if main_foods.exists():
                foods = main_foods
        
        elif meal_type == 'snack':
            # Snacks ligeros
            foods = foods.filter(calories__lte=250)
        
        # Seleccionar alimentos aleatorios
        foods_list = list(foods[:100])  # Limitar para performance
        selected_foods = random.sample(foods_list, min(count, len(foods_list)))
        
        # Crear respuesta simple
        recommendations = []
        for i, food in enumerate(selected_foods):
            # Cálculo simple de cantidad sugerida
            suggested_quantity = 100
            if food.calories > 300:
                suggested_quantity = 80
            elif food.calories < 100:
                suggested_quantity = 150
            
            # Cálculo nutricional para la cantidad
            factor = suggested_quantity / food.serving_size
            nutrition_for_quantity = {
                'calories': round(food.calories * factor, 1),
                'protein': round(food.protein * factor, 1),
                'carbs': round(food.carbohydrate * factor, 1),
                'fat': round(food.fat * factor, 1),
                'fiber': round(food.fiber * factor, 1)
            }
            
            # Generar razón simple
            reasons = []
            if food.protein >= 15:
                reasons.append("buena fuente de proteína")
            if food.fiber >= 3:
                reasons.append("contiene fibra")
            if food.calories <= 200:
                reasons.append("bajo en calorías")
            
            reason = f"Recomendado porque es {' y '.join(reasons) if reasons else 'una opción nutritiva'}."
            
            recommendations.append({
                'id': i + 1,
                'food': {
                    'id': food.id,
                    'display_name': food.name_es or food.name,
                    'category_name': food.category.name_es if food.category else 'Sin categoría',
                    'calories': food.calories,
                    'protein': food.protein,
                    'carbohydrate': food.carbohydrate,
                    'fat': food.fat
                },
                'total_score': random.randint(70, 95),  # Score aleatorio por ahora
                'nutrition_score': random.randint(60, 90),
                'preference_score': random.randint(50, 80),
                'variety_score': random.randint(70, 100),
                'suggested_quantity': suggested_quantity,
                'reason': reason,
                'nutrition_for_quantity': nutrition_for_quantity
            })
        
        return Response({
            'session': {
                'id': 1,
                'session_type': 'meal_suggestion', 
                'recommendations': recommendations
            },
            'message': f'Se encontraron {len(recommendations)} recomendaciones'
        })
        
    except Exception as e:
        return Response({
            'error': f'Error generando recomendaciones: {str(e)}',
            'debug_info': {
                'total_foods': Food.objects.count(),
                'meal_type': meal_type,
                'user_completed': user.profile_completed
            }
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)