# core/views.py
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Count, Sum

def home_view(request):
    """Página de inicio"""
    if request.user.is_authenticated:
        if request.user.profile_completed:
            return redirect('dashboard')
        else:
            return redirect('auth:profile_setup')
    
    return render(request, 'core/home.html')

@login_required
def dashboard_view(request):
    """Dashboard principal del usuario"""
    if not request.user.profile_completed:
        return redirect('auth:profile_setup')
    
    from recommendations.models import DailyNutritionLog, FoodConsumption
    from django.utils import timezone
    
    today = timezone.now().date()
    
    # Valores por defecto
    today_nutrition = {
        'calories': 0, 
        'protein': 0, 
        'carbs': 0, 
        'fat': 0, 
        'adherence_score': None
    }
    
    # Inicializar recent_foods vacío
    recent_foods = []
    
    try:
        daily_log = DailyNutritionLog.objects.get(user=request.user, date=today)
        today_nutrition = {
            'calories': daily_log.consumed_calories or 0,
            'protein': daily_log.consumed_protein or 0,
            'carbs': daily_log.consumed_carbs or 0,
            'fat': daily_log.consumed_fat or 0,
            'adherence_score': daily_log.adherence_score
        }
        print(f"DEBUG - Datos encontrados: {today_nutrition}")  # Debug adicional
        
        # Obtener comidas recientes del día
        recent_foods = FoodConsumption.objects.filter(
            daily_log=daily_log
        ).select_related('food').order_by('-timestamp')[:5]
        
    except DailyNutritionLog.DoesNotExist:
        print("DEBUG - No hay datos para hoy, usando valores por defecto")  # Debug adicional
        pass
    
    # Targets con valores por defecto
    nutrition_targets = {
        'calories': request.user.daily_calories or 2000,
        'protein': request.user.daily_protein or 150,
        'carbs': request.user.daily_carbs or 250,
        'fat': request.user.daily_fat or 65
    }
    
    print(f"DEBUG - Targets: {nutrition_targets}")  # Debug adicional
    
    # Calcular porcentajes de forma muy simple
    percentages = {}
    
    # Calorías
    if nutrition_targets['calories'] > 0:
        percentages['calories'] = round((today_nutrition['calories'] / nutrition_targets['calories']) * 100, 1)
    else:
        percentages['calories'] = 0
    
    # Proteína
    if nutrition_targets['protein'] > 0:
        percentages['protein'] = round((today_nutrition['protein'] / nutrition_targets['protein']) * 100, 1)
    else:
        percentages['protein'] = 0
    
    # Carbohidratos
    if nutrition_targets['carbs'] > 0:
        percentages['carbs'] = round((today_nutrition['carbs'] / nutrition_targets['carbs']) * 100, 1)
    else:
        percentages['carbs'] = 0
    
    # Grasas
    if nutrition_targets['fat'] > 0:
        percentages['fat'] = round((today_nutrition['fat'] / nutrition_targets['fat']) * 100, 1)
    else:
        percentages['fat'] = 0
    
    # Limitar a 100% máximo
    for key in percentages:
        if percentages[key] > 100:
            percentages[key] = 100
    
    print(f"DEBUG - Percentages: {percentages}")  # Para debug original
    
    context = {
        'user': request.user,
        'today_nutrition': today_nutrition,
        'nutrition_targets': nutrition_targets,
        'percentages': percentages,
        'recent_foods': recent_foods  # Agregado de la segunda función
    }
    
    return render(request, 'core/dashboard.html', context)

def api_status(request):
    """Estado de la API"""
    return JsonResponse({
        'status': 'NutriMatch API funcionando',
        'version': '1.0',
        'authenticated': request.user.is_authenticated,
        'user': request.user.username if request.user.is_authenticated else None
    })

@login_required
def progress_view(request):
    """Página completa de progreso del usuario"""
    from recommendations.models import DailyNutritionLog, FoodConsumption
    from django.utils import timezone
    from datetime import timedelta
    import json
    
    user = request.user
    
    # Obtener datos de los últimos 30 días
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=29)
    
    daily_logs = DailyNutritionLog.objects.filter(
        user=user,
        date__range=[start_date, end_date]
    ).order_by('date')
    
    # Preparar datos para gráficos
    chart_data = {
        'dates': [],
        'calories': [],
        'protein': [],
        'carbs': [],
        'fat': [],
        'adherence': []
    }
    
    for log in daily_logs:
        chart_data['dates'].append(log.date.strftime('%d/%m'))
        chart_data['calories'].append(float(log.consumed_calories or 0))
        chart_data['protein'].append(float(log.consumed_protein or 0))
        chart_data['carbs'].append(float(log.consumed_carbs or 0))
        chart_data['fat'].append(float(log.consumed_fat or 0))
        chart_data['adherence'].append(float(log.adherence_score or 0))
    
    # Debug: Imprimir los datos para verificar
    print("Chart data:", chart_data)
    
    # Estadísticas generales
    if daily_logs:
        avg_calories = sum(log.consumed_calories or 0 for log in daily_logs) / len(daily_logs)
        avg_protein = sum(log.consumed_protein or 0 for log in daily_logs) / len(daily_logs)
        avg_adherence = sum(log.adherence_score or 0 for log in daily_logs) / len(daily_logs)
        
        # Encontrar el mejor día (el que tenga mayor adherencia)
        best_day = None
        max_adherence = 0
        for log in daily_logs:
            if (log.adherence_score or 0) > max_adherence:
                max_adherence = log.adherence_score or 0
                best_day = log
        
        total_days_logged = daily_logs.count()
    else:
        avg_calories = avg_protein = avg_adherence = 0
        best_day = None
        total_days_logged = 0
    
    # Alimentos más consumidos
    popular_foods = FoodConsumption.objects.filter(
        daily_log__user=user,
        daily_log__date__range=[start_date, end_date]
    ).values(
        'food__name', 'food__name_es'
    ).annotate(
        total_consumed=Count('food'),
        total_calories=Sum('calories_consumed')
    ).order_by('-total_consumed')[:10]
    
    # Progreso por objetivos
    targets = {
        'calories': user.daily_calories or 2000,
        'protein': user.daily_protein or 150,
        'carbs': user.daily_carbs or 250,
        'fat': user.daily_fat or 65
    }
    
    # Verificar si la proteína promedio está por debajo del 80% del objetivo
    protein_target = targets['protein']
    protein_low_warning = avg_protein < (protein_target * 0.8)
    
    context = {
        'chart_data_json': json.dumps(chart_data, ensure_ascii=False),
        'statistics': {
            'avg_calories': round(avg_calories, 1),
            'avg_protein': round(avg_protein, 1),
            'avg_adherence': round(avg_adherence, 1),
            'total_days': total_days_logged,
            'best_day': best_day,
            'targets': targets,
            'protein_low_warning': protein_low_warning
        },
        'popular_foods': popular_foods,
        'date_range': f"{start_date.strftime('%d/%m')} - {end_date.strftime('%d/%m')}"
    }
    
    return render(request, 'core/progress.html', context)
