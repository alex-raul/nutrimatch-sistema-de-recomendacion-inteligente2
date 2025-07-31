# recommendations/urls.py
from django.urls import path
from . import views

app_name = 'recommendations'

urlpatterns = [
    # Recomendaciones principales
    path('get-recommendations/', views.get_recommendations, name='get-recommendations'),
    path('feedback/', views.recommendation_feedback, name='recommendation-feedback'),
    
    # Registro de consumo y calificaciones
    path('log-consumption/', views.log_food_consumption, name='log-consumption'),
    path('rate-food/', views.rate_food, name='rate-food'),
    path('ratings/', views.UserFoodRatingListView.as_view(), name='food-ratings'),
    
    # Análisis y seguimiento
    path('daily-summary/', views.daily_nutrition_summary, name='daily-summary'),
    path('insights/', views.user_nutrition_insights, name='nutrition-insights'),
    
    # Perfil nutricional
    path('nutritional-profile/', views.NutritionalProfileView.as_view(), name='nutritional-profile'),

    path('get-simple-recommendations/', views.get_simple_recommendations, name='get-simple-recommendations'),
]