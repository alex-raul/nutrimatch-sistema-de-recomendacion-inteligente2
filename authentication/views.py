# authentication/views.py
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.authtoken.models import Token
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
import json

from users.models import CustomUser
from users.serializers import UserRegistrationSerializer, UserProfileSerializer

# Vistas basadas en HTML
def login_view(request):
    """Página de login"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            # Configurar duración de sesión
            if not remember_me:
                request.session.set_expiry(0)  # Expira al cerrar navegador
            
            messages.success(request, f'¡Bienvenido de vuelta, {user.first_name or user.username}!')
            
            # Redirigir según el estado del perfil
            if user.profile_completed:
                return redirect('dashboard')
            else:
                return redirect('auth:profile_setup')  # Cambio aquí: agregar 'auth:'
        else:
            messages.error(request, 'Usuario o contraseña incorrectos.')
    
    return render(request, 'authentication/login.html')

def register_view(request):
    """Página de registro"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        
        # Validaciones
        errors = []
        
        if CustomUser.objects.filter(username=username).exists():
            errors.append('El nombre de usuario ya existe.')
        
        if CustomUser.objects.filter(email=email).exists():
            errors.append('El email ya está registrado.')
        
        if password != password_confirm:
            errors.append('Las contraseñas no coinciden.')
        
        if len(password) < 8:
            errors.append('La contraseña debe tener al menos 8 caracteres.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
        else:
            # Crear usuario
            user = CustomUser.objects.create_user(
                username=username,
                email=email,
                password=password,
                first_name=first_name,
                last_name=last_name
            )
            
            messages.success(request, '¡Cuenta creada exitosamente! Ahora completa tu perfil.')
            
            # Login automático
            login(request, user)
            return redirect('auth:profile_setup')  # Cambio aquí: agregar 'auth:'
    
    return render(request, 'authentication/register.html')

@login_required
def logout_view(request):
    """Cerrar sesión"""
    username = request.user.first_name or request.user.username
    logout(request)
    messages.success(request, f'¡Hasta luego, {username}!')
    return redirect('home')

@login_required
def profile_setup_view(request):
    """Configuración inicial del perfil"""
    user = request.user
    
    if user.profile_completed:
        return redirect('dashboard')
    
    if request.method == 'POST':
        # Actualizar información personal
        user.age = int(request.POST.get('age')) if request.POST.get('age') else None
        user.weight = float(request.POST.get('weight')) if request.POST.get('weight') else None
        user.height = float(request.POST.get('height')) if request.POST.get('height') else None
        user.gender = request.POST.get('gender')
        user.goal = request.POST.get('goal')
        user.activity_level = request.POST.get('activity_level')
        
        # Calcular necesidades nutricionales
        if all([user.age, user.weight, user.height, user.gender, user.goal]):
            user.daily_calories = user.calculate_daily_calories()
            
            # Calcular distribución de macronutrientes
            if user.goal == 'lose_weight':
                protein_ratio, carb_ratio, fat_ratio = 0.30, 0.35, 0.35
            elif user.goal == 'build_muscle':
                protein_ratio, carb_ratio, fat_ratio = 0.30, 0.40, 0.30
            elif user.goal == 'gain_weight':
                protein_ratio, carb_ratio, fat_ratio = 0.25, 0.45, 0.30
            else:  # maintain_weight, improve_health
                protein_ratio, carb_ratio, fat_ratio = 0.25, 0.45, 0.30
            
            user.daily_protein = round((user.daily_calories * protein_ratio) / 4, 1)
            user.daily_carbs = round((user.daily_calories * carb_ratio) / 4, 1)
            user.daily_fat = round((user.daily_calories * fat_ratio) / 9, 1)
            
            user.profile_completed = True
        
        user.save()
        
        # Crear/actualizar preferencias
        from users.models import UserPreference
        preferences, created = UserPreference.objects.get_or_create(user=user)
        preferences.is_vegetarian = 'vegetarian' in request.POST.getlist('dietary_preferences')
        preferences.is_vegan = 'vegan' in request.POST.getlist('dietary_preferences')
        preferences.is_gluten_free = 'gluten_free' in request.POST.getlist('dietary_preferences')
        preferences.is_dairy_free = 'dairy_free' in request.POST.getlist('dietary_preferences')
        preferences.is_keto = 'keto' in request.POST.getlist('dietary_preferences')
        preferences.preferred_meal_count = int(request.POST.get('meal_count', 3))
        preferences.budget_preference = request.POST.get('budget_preference', 'medium')
        preferences.save()
        
        # NUEVO: Crear perfil nutricional
        from recommendations.models import NutritionalProfile
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
        
        messages.success(request, '¡Perfil completado! Bienvenido a NutriMatch.')
        return redirect('dashboard')
    
    return render(request, 'authentication/profile_setup.html', {
        'user': user,
        'goals': CustomUser.GOAL_CHOICES,
        'activity_levels': CustomUser.ACTIVITY_CHOICES,
        'genders': CustomUser.GENDER_CHOICES,
    })
# APIs para aplicaciones móviles/SPA
@api_view(['POST'])
@permission_classes([AllowAny])
def api_register(request):
    """API de registro"""
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'message': 'Usuario creado exitosamente',
            'user': UserProfileSerializer(user).data,
            'token': token.key
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([AllowAny])
def api_login(request):
    """API de login"""
    username = request.data.get('username')
    password = request.data.get('password')
    
    if not username or not password:
        return Response({
            'error': 'Username y password son requeridos'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(username=username, password=password)
    if user:
        token, created = Token.objects.get_or_create(user=user)
        
        return Response({
            'message': 'Login exitoso',
            'user': UserProfileSerializer(user).data,
            'token': token.key,
            'profile_completed': user.profile_completed
        })
    
    return Response({
        'error': 'Credenciales inválidas'
    }, status=status.HTTP_401_UNAUTHORIZED)

@api_view(['POST'])
def api_logout(request):
    """API de logout"""
    try:
        request.user.auth_token.delete()
        return Response({'message': 'Logout exitoso'})
    except:
        return Response({'message': 'Logout exitoso'})

@api_view(['GET'])
def api_profile(request):
    """API para obtener perfil del usuario"""
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)

@api_view(['POST'])
def api_change_password(request):
    """API para cambiar contraseña"""
    user = request.user
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')
    
    if not user.check_password(current_password):
        return Response({
            'error': 'Contraseña actual incorrecta'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if len(new_password) < 8:
        return Response({
            'error': 'La nueva contraseña debe tener al menos 8 caracteres'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user.set_password(new_password)
    user.save()
    
    # Regenerar token
    user.auth_token.delete()
    token = Token.objects.create(user=user)
    
    return Response({
        'message': 'Contraseña actualizada exitosamente',
        'token': token.key
    })