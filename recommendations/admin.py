# recommendations/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import (
    UserFoodRating, NutritionalProfile, DailyNutritionLog, 
    FoodConsumption, RecommendationSession, Recommendation,
    UserFoodPreference, SimilarFood
)

@admin.register(UserFoodRating)
class UserFoodRatingAdmin(admin.ModelAdmin):
    list_display = ('user', 'food', 'rating_stars', 'meal_type', 'created_at')
    list_filter = ('rating', 'meal_type', 'created_at')
    search_fields = ('user__username', 'food__name', 'food__name_es')
    autocomplete_fields = ['user', 'food']
    
    def rating_stars(self, obj):
        stars = '⭐' * obj.rating
        return format_html('<span title="{} estrellas">{}</span>', obj.rating, stars)
    rating_stars.short_description = 'Calificación'

@admin.register(NutritionalProfile)
class NutritionalProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'target_calories', 'target_protein', 'target_carbs', 'target_fat')
    search_fields = ('user__username',)
    autocomplete_fields = ['user']
    
    fieldsets = (
        ('Objetivos Diarios', {
            'fields': ('target_calories', 'target_protein', 'target_carbs', 'target_fat', 'target_fiber')
        }),
        ('Límites de Micronutrientes', {
            'fields': ('max_sodium', 'min_calcium', 'min_iron', 'min_vitamin_c'),
            'classes': ('collapse',)
        }),
        ('Factores de Peso', {
            'fields': ('protein_importance', 'health_importance', 'taste_importance'),
            'classes': ('collapse',)
        }),
    )

@admin.register(DailyNutritionLog)
class DailyNutritionLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'date', 'consumed_calories', 'adherence_score', 'balance_score', 'water_glasses')
    list_filter = ('date', 'adherence_score')
    search_fields = ('user__username',)
    autocomplete_fields = ['user']
    date_hierarchy = 'date'
    
    readonly_fields = ('adherence_score', 'balance_score')
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('user', 'date', 'water_glasses')
        }),
        ('Consumo Nutricional', {
            'fields': ('consumed_calories', 'consumed_protein', 'consumed_carbs', 'consumed_fat', 'consumed_fiber', 'consumed_sodium')
        }),
        ('Métricas', {
            'fields': ('adherence_score', 'balance_score'),
            'classes': ('collapse',)
        }),
    )

@admin.register(FoodConsumption)
class FoodConsumptionAdmin(admin.ModelAdmin):
    list_display = ('daily_log', 'food', 'quantity', 'meal_type', 'calories_consumed', 'timestamp')
    list_filter = ('meal_type', 'timestamp')
    search_fields = ('daily_log__user__username', 'food__name', 'food__name_es')
    autocomplete_fields = ['daily_log', 'food']
    
    readonly_fields = ('calories_consumed', 'protein_consumed', 'carbs_consumed', 'fat_consumed')

@admin.register(RecommendationSession)
class RecommendationSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'session_type', 'recommendation_count', 'created_at')
    list_filter = ('session_type', 'created_at')
    search_fields = ('user__username',)
    autocomplete_fields = ['user']
    
    def recommendation_count(self, obj):
        return obj.recommendations.count()
    recommendation_count.short_description = 'Recomendaciones'

@admin.register(Recommendation)
class RecommendationAdmin(admin.ModelAdmin):
    list_display = ('session_user', 'food', 'total_score', 'position', 'user_feedback', 'created_at')
    list_filter = ('user_feedback', 'created_at')
    search_fields = ('session__user__username', 'food__name', 'food__name_es')
    autocomplete_fields = ['session', 'food']
    
    readonly_fields = ('created_at',)
    
    def session_user(self, obj):
        return obj.session.user.username
    session_user.short_description = 'Usuario'

@admin.register(UserFoodPreference)
class UserFoodPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'food', 'preference_score', 'frequency_consumed', 'confidence', 'last_consumed')
    list_filter = ('confidence', 'last_consumed')
    search_fields = ('user__username', 'food__name', 'food__name_es')
    autocomplete_fields = ['user', 'food']

@admin.register(SimilarFood)
class SimilarFoodAdmin(admin.ModelAdmin):
    list_display = ('food1', 'food2', 'overall_similarity', 'nutritional_similarity', 'macro_similarity')
    search_fields = ('food1__name', 'food1__name_es', 'food2__name', 'food2__name_es')
    autocomplete_fields = ['food1', 'food2']
    
    list_filter = ('overall_similarity',)