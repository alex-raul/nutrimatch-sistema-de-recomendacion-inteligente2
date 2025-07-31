# users/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import UserAllergy, UserPreference

User = get_user_model()

class UserAllergySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAllergy
        fields = ['id', 'allergen', 'severity']

class UserPreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreference
        fields = [
            'is_vegetarian', 'is_vegan', 'is_gluten_free', 'is_dairy_free', 'is_keto',
            'preferred_meal_count', 'max_prep_time', 'budget_preference'
        ]

class UserProfileSerializer(serializers.ModelSerializer):
    allergies = UserAllergySerializer(many=True, read_only=True)
    preferences = UserPreferenceSerializer(read_only=True)
    bmr = serializers.SerializerMethodField()
    daily_calories_calculated = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'age', 'weight', 'height', 'gender', 'goal', 'activity_level',
            'daily_calories', 'daily_protein', 'daily_carbs', 'daily_fat',
            'profile_completed', 'allergies', 'preferences',
            'bmr', 'daily_calories_calculated'
        ]
        read_only_fields = ['id', 'username']
    
    def get_bmr(self, obj):
        return obj.calculate_bmr()
    
    def get_daily_calories_calculated(self, obj):
        return obj.calculate_daily_calories()

class UserRegistrationSerializer(serializers.ModelSerializer):
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name'
        ]
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Las contraseñas no coinciden")
        return data
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user

class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'age', 'weight', 'height', 
            'gender', 'goal', 'activity_level'
        ]
    
    def update(self, instance, validated_data):
        user = super().update(instance, validated_data)
        
        # Recalcular necesidades nutricionales si cambió información relevante
        if any(field in validated_data for field in ['weight', 'height', 'age', 'gender', 'goal', 'activity_level']):
            user.daily_calories = user.calculate_daily_calories()
            user.profile_completed = all([user.weight, user.height, user.age, user.gender, user.goal])
            user.save()
        
        return user