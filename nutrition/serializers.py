# nutrition/serializers.py
from rest_framework import serializers
from .models import Food, FoodCategory, FoodAlias

class FoodCategorySerializer(serializers.ModelSerializer):
    food_count = serializers.SerializerMethodField()
    
    class Meta:
        model = FoodCategory
        fields = ['id', 'name', 'name_es', 'description', 'color', 'food_count']
    
    def get_food_count(self, obj):
        return obj.food_set.count()

class FoodListSerializer(serializers.ModelSerializer):
    """Serializer para lista de alimentos (campos básicos)"""
    category_name = serializers.CharField(source='category.name_es', read_only=True)
    display_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Food
        fields = [
            'id', 'display_name', 'category_name', 'calories', 
            'protein', 'carbohydrate', 'fat', 'fiber',
            'protein_density', 'nutrient_density_score'
        ]
    
    def get_display_name(self, obj):
        return obj.name_es or obj.name

class FoodDetailSerializer(serializers.ModelSerializer):
    """Serializer completo para detalles de alimento"""
    category = FoodCategorySerializer(read_only=True)
    display_name = serializers.SerializerMethodField()
    aliases = serializers.StringRelatedField(many=True, read_only=True)
    
    # Campos calculados
    macronutrient_breakdown = serializers.SerializerMethodField()
    key_vitamins = serializers.SerializerMethodField()
    key_minerals = serializers.SerializerMethodField()
    
    class Meta:
        model = Food
        fields = [
            'id', 'display_name', 'name', 'category', 'serving_size',
            'calories', 'protein', 'carbohydrate', 'fat', 'fiber', 'sugars',
            'total_fat', 'saturated_fat', 'monounsaturated_fat', 'polyunsaturated_fat',
            'trans_fat', 'cholesterol', 'sodium', 'potassium', 'calcium', 'iron',
            'magnesium', 'phosphorus', 'zinc', 'vitamin_a', 'vitamin_c', 'vitamin_d',
            'vitamin_e', 'vitamin_k', 'thiamin', 'riboflavin', 'niacin', 'vitamin_b6',
            'vitamin_b12', 'folate', 'protein_density', 'nutrient_density_score',
            'aliases', 'macronutrient_breakdown', 'key_vitamins', 'key_minerals',
            'is_verified', 'data_source'
        ]
    
    def get_display_name(self, obj):
        return obj.name_es or obj.name
    
    def get_macronutrient_breakdown(self, obj):
        """Breakdown porcentual de macronutrientes"""
        total_calories = obj.calories
        if total_calories == 0:
            return {'protein': 0, 'carbs': 0, 'fat': 0}
        
        protein_cals = obj.protein * 4
        carb_cals = obj.carbohydrate * 4
        fat_cals = obj.fat * 9
        
        return {
            'protein': round((protein_cals / total_calories) * 100, 1),
            'carbs': round((carb_cals / total_calories) * 100, 1),
            'fat': round((fat_cals / total_calories) * 100, 1)
        }
    
    def get_key_vitamins(self, obj):
        """Vitaminas más importantes"""
        return {
            'vitamin_a': obj.vitamin_a,
            'vitamin_c': obj.vitamin_c,
            'vitamin_d': obj.vitamin_d,
            'vitamin_b12': obj.vitamin_b12,
            'folate': obj.folate
        }
    
    def get_key_minerals(self, obj):
        """Minerales más importantes"""
        return {
            'calcium': obj.calcium,
            'iron': obj.iron,
            'magnesium': obj.magnesium,
            'potassium': obj.potassium,
            'sodium': obj.sodium,
            'zinc': obj.zinc
        }

class FoodSearchSerializer(serializers.ModelSerializer):
    """Serializer optimizado para búsquedas"""
    display_name = serializers.SerializerMethodField()
    category_name = serializers.CharField(source='category.name_es', read_only=True)
    nutrition_summary = serializers.SerializerMethodField()
    
    class Meta:
        model = Food
        fields = [
            'id', 'display_name', 'category_name', 'serving_size',
            'nutrition_summary', 'protein_density'
        ]
    
    def get_display_name(self, obj):
        return obj.name_es or obj.name
    
    def get_nutrition_summary(self, obj):
        return {
            'calories': obj.calories,
            'protein': obj.protein,
            'carbs': obj.carbohydrate,
            'fat': obj.fat,
            'fiber': obj.fiber
        }