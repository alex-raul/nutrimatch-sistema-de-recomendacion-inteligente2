# users/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class CustomUser(AbstractUser):
    """Usuario extendido con información nutricional"""
    
    # Información básica
    age = models.PositiveIntegerField(null=True, blank=True)
    weight = models.FloatField(null=True, blank=True, help_text="Peso en kg")
    height = models.FloatField(null=True, blank=True, help_text="Altura en cm")
    
    GENDER_CHOICES = [
        ('M', 'Masculino'),
        ('F', 'Femenino'),
        ('O', 'Otro'),
    ]
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    
    # Objetivos y actividad
    GOAL_CHOICES = [
        ('lose_weight', 'Perder peso'),
        ('maintain_weight', 'Mantener peso'),
        ('gain_weight', 'Ganar peso'),
        ('build_muscle', 'Ganar músculo'),
        ('improve_health', 'Mejorar salud'),
    ]
    goal = models.CharField(max_length=20, choices=GOAL_CHOICES, null=True, blank=True)
    
    ACTIVITY_CHOICES = [
        ('sedentary', 'Sedentario'),
        ('light', 'Actividad ligera'),
        ('moderate', 'Actividad moderada'),
        ('active', 'Muy activo'),
        ('extra_active', 'Extremadamente activo'),
    ]
    activity_level = models.CharField(max_length=15, choices=ACTIVITY_CHOICES, default='moderate')
    
    # Necesidades nutricionales calculadas
    daily_calories = models.IntegerField(null=True, blank=True)
    daily_protein = models.FloatField(null=True, blank=True)
    daily_carbs = models.FloatField(null=True, blank=True)
    daily_fat = models.FloatField(null=True, blank=True)
    
    # Timestamps
    profile_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.username} - {self.get_goal_display()}"
    
    def calculate_bmr(self):
        """Calcular Tasa Metabólica Basal usando fórmula Harris-Benedict"""
        if not all([self.weight, self.height, self.age, self.gender]):
            return None
            
        if self.gender == 'M':
            bmr = 88.362 + (13.397 * self.weight) + (4.799 * self.height) - (5.677 * self.age)
        else:
            bmr = 447.593 + (9.247 * self.weight) + (3.098 * self.height) - (4.330 * self.age)
        
        return round(bmr, 2)
    
    def calculate_daily_calories(self):
        """Calcular calorías diarias basado en actividad"""
        bmr = self.calculate_bmr()
        if not bmr:
            return None
            
        activity_multipliers = {
            'sedentary': 1.2,
            'light': 1.375,
            'moderate': 1.55,
            'active': 1.725,
            'extra_active': 1.9,
        }
        
        calories = bmr * activity_multipliers.get(self.activity_level, 1.55)
        
        # Ajustar según objetivo
        if self.goal == 'lose_weight':
            calories *= 0.85  # Déficit del 15%
        elif self.goal == 'gain_weight':
            calories *= 1.15  # Superávit del 15%
        
        return round(calories)

class UserAllergy(models.Model):
    """Alergias del usuario"""
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='allergies')
    allergen = models.CharField(max_length=100)
    severity = models.CharField(max_length=20, choices=[
        ('mild', 'Leve'),
        ('moderate', 'Moderada'),
        ('severe', 'Severa'),
    ], default='moderate')
    
    class Meta:
        unique_together = ('user', 'allergen')

class UserPreference(models.Model):
    """Preferencias alimentarias del usuario"""
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='preferences')
    
    # Restricciones dietéticas
    is_vegetarian = models.BooleanField(default=False)
    is_vegan = models.BooleanField(default=False)
    is_gluten_free = models.BooleanField(default=False)
    is_dairy_free = models.BooleanField(default=False)
    is_keto = models.BooleanField(default=False)
    
    # Preferencias generales
    preferred_meal_count = models.IntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(8)])
    max_prep_time = models.IntegerField(default=30, help_text="Tiempo máximo de preparación en minutos")
    budget_preference = models.CharField(max_length=20, choices=[
        ('low', 'Económico'),
        ('medium', 'Moderado'),
        ('high', 'Sin restricción'),
    ], default='medium')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

class Meta:
    verbose_name = "Usuario"
    verbose_name_plural = "Usuarios"