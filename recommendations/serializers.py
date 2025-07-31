# recommendations/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    UserFoodRating, NutritionalProfile, DailyNutritionLog,
    FoodConsumption, RecommendationSession, Recommendation,
    UserFoodPreference, SimilarFood
)
from nutrition.serializers import FoodListSerializer

User = get_user_model()

class UserFoodRatingSerializer(serializers.ModelSerializer):
    food_name = serializers.CharField(source='food.name_es', read_only=True)
    
    class Meta:
        model = UserFoodRating
        fields = ['id', 'food', 'food_name', 'rating', 'notes', 'meal_type', 'created_at']
        read_only_fields = ['id', 'created_at']

class NutritionalProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = NutritionalProfile
        fields = [
            'target_calories', 'target_protein', 'target_carbs', 'target_fat',
            'target_fiber', 'max_sodium', 'min_calcium', 'min_iron', 'min_vitamin_c',
            'protein_importance', 'health_importance', 'taste_importance'
        ]

class FoodConsumptionSerializer(serializers.ModelSerializer):
    food_name = serializers.CharField(source='food.name_es', read_only=True)
    food_category = serializers.CharField(source='food.category.name_es', read_only=True)
    
    class Meta:
        model = FoodConsumption
        fields = [
            'id', 'food', 'food_name', 'food_category', 'quantity', 'meal_type',
            'calories_consumed', 'protein_consumed', 'carbs_consumed', 'fat_consumed',
            'timestamp'
        ]
        read_only_fields = ['calories_consumed', 'protein_consumed', 'carbs_consumed', 'fat_consumed']

class DailyNutritionLogSerializer(serializers.ModelSerializer):
    food_consumptions = FoodConsumptionSerializer(many=True, read_only=True)
    adherence_percentage = serializers.SerializerMethodField()
    remaining_nutrients = serializers.SerializerMethodField()
    
    class Meta:
        model = DailyNutritionLog
        fields = [
            'id', 'date', 'consumed_calories', 'consumed_protein', 'consumed_carbs',
            'consumed_fat', 'consumed_fiber', 'consumed_sodium', 'water_glasses',
            'adherence_score', 'balance_score', 'food_consumptions',
            'adherence_percentage', 'remaining_nutrients'
        ]
        read_only_fields = ['adherence_score', 'balance_score']
    
    def get_adherence_percentage(self, obj):
        return obj.calculate_adherence_score()
    
    def get_remaining_nutrients(self, obj):
        user_profile = getattr(obj.user, 'nutritional_profile', None)
        if not user_profile:
            return None
        
        return {
            'calories': max(0, user_profile.target_calories - obj.consumed_calories),
            'protein': max(0, user_profile.target_protein - obj.consumed_protein),
            'carbs': max(0, user_profile.target_carbs - obj.consumed_carbs),
            'fat': max(0, user_profile.target_fat - obj.consumed_fat),
            'fiber': max(0, user_profile.target_fiber - obj.consumed_fiber)
        }

class RecommendationSerializer(serializers.ModelSerializer):
    food = FoodListSerializer(read_only=True)
    nutrition_for_quantity = serializers.SerializerMethodField()
    
    class Meta:
        model = Recommendation
        fields = [
            'id', 'food', 'total_score', 'nutrition_score', 'preference_score',
            'variety_score', 'suggested_quantity', 'reason', 'position',
            'nutrition_for_quantity'
        ]
    
    def get_nutrition_for_quantity(self, obj):
        """Calcular nutrición para la cantidad sugerida"""
        factor = obj.suggested_quantity / obj.food.serving_size
        return {
            'calories': round(obj.food.calories * factor, 1),
            'protein': round(obj.food.protein * factor, 1),
            'carbs': round(obj.food.carbohydrate * factor, 1),
            'fat': round(obj.food.fat * factor, 1),
            'fiber': round(obj.food.fiber * factor, 1)
        }

class RecommendationSessionSerializer(serializers.ModelSerializer):
    recommendations = RecommendationSerializer(many=True, read_only=True)
    
    class Meta:
        model = RecommendationSession
        fields = [
            'id', 'session_type', 'current_nutrition', 'user_preferences',
            'created_at', 'recommendations'
        ]

class UserFoodPreferenceSerializer(serializers.ModelSerializer):
    food_name = serializers.CharField(source='food.name_es', read_only=True)
    
    class Meta:
        model = UserFoodPreference
        fields = [
            'food', 'food_name', 'preference_score', 'frequency_consumed',
            'last_consumed', 'preferred_meal_types', 'confidence'
        ]