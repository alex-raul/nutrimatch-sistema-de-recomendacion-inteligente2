# users/views.py
from rest_framework import generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.contrib.auth import authenticate, login
from .models import CustomUser, UserPreference
from .serializers import (
    UserProfileSerializer, UserRegistrationSerializer, 
    UserUpdateSerializer, UserPreferenceSerializer
)

class UserRegistrationView(generics.CreateAPIView):
    """Registro de nuevos usuarios"""
    queryset = CustomUser.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = []  # Público

class UserProfileView(generics.RetrieveUpdateAPIView):
    """Ver y actualizar perfil de usuario"""
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user

class UserUpdateView(generics.UpdateAPIView):
    """Actualizar información básica del usuario"""
    serializer_class = UserUpdateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user

@api_view(['GET', 'PUT'])
@permission_classes([IsAuthenticated])
def user_preferences(request):
    """Gestionar preferencias del usuario"""
    user = request.user
    
    if request.method == 'GET':
        preferences, created = UserPreference.objects.get_or_create(user=user)
        serializer = UserPreferenceSerializer(preferences)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        preferences, created = UserPreference.objects.get_or_create(user=user)
        serializer = UserPreferenceSerializer(preferences, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def complete_profile_setup(request):
    """Completar configuración inicial del perfil"""
    user = request.user
    
    # Actualizar información del usuario
    user_data = {
        'age': request.data.get('age'),
        'weight': request.data.get('weight'),
        'height': request.data.get('height'),
        'gender': request.data.get('gender'),
        'goal': request.data.get('goal'),
        'activity_level': request.data.get('activity_level'),
    }
    
    user_serializer = UserUpdateSerializer(user, data=user_data, partial=True)
    if not user_serializer.is_valid():
        return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    user_serializer.save()
    
    # Crear/actualizar preferencias
    preferences_data = request.data.get('preferences', {})
    preferences, created = UserPreference.objects.get_or_create(user=user)
    preferences_serializer = UserPreferenceSerializer(
        preferences, data=preferences_data, partial=True
    )
    
    if preferences_serializer.is_valid():
        preferences_serializer.save()
    
    # Marcar perfil como completado
    user.profile_completed = True
    user.save()
    
    return Response({
        'message': 'Perfil completado exitosamente',
        'user': UserProfileSerializer(user).data
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def nutrition_goals(request):
    """Obtener objetivos nutricionales del usuario"""
    user = request.user
    
    if not user.profile_completed:
        return Response({
            'error': 'Perfil no completado. Complete su información primero.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    bmr = user.calculate_bmr()
    daily_calories = user.calculate_daily_calories()
    
    # Calcular distribución de macronutrientes según objetivo
    if user.goal == 'lose_weight':
        protein_ratio = 0.30
        carb_ratio = 0.35
        fat_ratio = 0.35
    elif user.goal == 'build_muscle':
        protein_ratio = 0.30
        carb_ratio = 0.40
        fat_ratio = 0.30
    elif user.goal == 'gain_weight':
        protein_ratio = 0.25
        carb_ratio = 0.45
        fat_ratio = 0.30
    else:  # maintain_weight, improve_health
        protein_ratio = 0.25
        carb_ratio = 0.45
        fat_ratio = 0.30
    
    daily_protein = (daily_calories * protein_ratio) / 4  # 4 cal/g
    daily_carbs = (daily_calories * carb_ratio) / 4  # 4 cal/g
    daily_fat = (daily_calories * fat_ratio) / 9  # 9 cal/g
    
    # Actualizar en el usuario
    user.daily_calories = daily_calories
    user.daily_protein = round(daily_protein, 1)
    user.daily_carbs = round(daily_carbs, 1)
    user.daily_fat = round(daily_fat, 1)
    user.save()
    
    return Response({
        'bmr': bmr,
        'daily_calories': daily_calories,
        'macronutrients': {
            'protein': {'grams': user.daily_protein, 'percentage': protein_ratio * 100},
            'carbohydrates': {'grams': user.daily_carbs, 'percentage': carb_ratio * 100},
            'fat': {'grams': user.daily_fat, 'percentage': fat_ratio * 100},
        },
        'goal': user.get_goal_display(),
        'activity_level': user.get_activity_level_display()
    })