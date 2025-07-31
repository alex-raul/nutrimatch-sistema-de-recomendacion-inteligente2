# recommendations/models.py
from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from nutrition.models import Food
import json

User = get_user_model()

class UserFoodRating(models.Model):
    """Calificaciones de alimentos por usuario"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Calificación de 1 a 5 estrellas"
    )
    notes = models.TextField(blank=True, help_text="Notas opcionales del usuario")
    
    # Contexto de la calificación
    meal_type = models.CharField(max_length=20, choices=[
        ('breakfast', 'Desayuno'),
        ('lunch', 'Almuerzo'),
        ('dinner', 'Cena'),
        ('snack', 'Snack'),
    ], null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'food')
        indexes = [
            models.Index(fields=['user', 'rating']),
            models.Index(fields=['food', 'rating']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.food.name} ({self.rating}⭐)"

class NutritionalProfile(models.Model):
    """Perfil nutricional calculado del usuario"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='nutritional_profile')
    
    # Necesidades diarias calculadas
    target_calories = models.IntegerField()
    target_protein = models.FloatField()
    target_carbs = models.FloatField()
    target_fat = models.FloatField()
    target_fiber = models.FloatField(default=25)
    
    # Límites de micronutrientes
    max_sodium = models.FloatField(default=2300)  # mg
    min_calcium = models.FloatField(default=1000)  # mg
    min_iron = models.FloatField(default=8)  # mg
    min_vitamin_c = models.FloatField(default=90)  # mg
    
    # Factores de peso para recomendaciones
    protein_importance = models.FloatField(default=1.0, validators=[MinValueValidator(0), MaxValueValidator(2)])
    health_importance = models.FloatField(default=1.0, validators=[MinValueValidator(0), MaxValueValidator(2)])
    taste_importance = models.FloatField(default=1.0, validators=[MinValueValidator(0), MaxValueValidator(2)])
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Perfil nutricional de {self.user.username}"

class DailyNutritionLog(models.Model):
    """Registro diario de nutrición del usuario"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    date = models.DateField()
    
    # Consumo actual del día
    consumed_calories = models.FloatField(default=0)
    consumed_protein = models.FloatField(default=0)
    consumed_carbs = models.FloatField(default=0)
    consumed_fat = models.FloatField(default=0)
    consumed_fiber = models.FloatField(default=0)
    consumed_sodium = models.FloatField(default=0)
    
    # Control de agua
    water_glasses = models.IntegerField(default=0, help_text="Vasos de agua consumidos")
    
    # Métricas del día
    adherence_score = models.FloatField(null=True, blank=True, help_text="Score de adherencia 0-100")
    balance_score = models.FloatField(null=True, blank=True, help_text="Score de balance nutricional 0-100")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'date')
        indexes = [
            models.Index(fields=['user', 'date']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.date}"
    
    def calculate_adherence_score(self):
        """Calcular qué tan bien se adhiere a sus objetivos"""
        try:
            profile = self.user.nutritional_profile
        except:
            # Si no existe perfil nutricional, crearlo o usar valores por defecto
            return self._calculate_adherence_with_defaults()
        
        if not profile:
            return self._calculate_adherence_with_defaults()
        
        # Calcular desviación de objetivos
        calorie_adherence = min(100, (self.consumed_calories / profile.target_calories) * 100) if profile.target_calories > 0 else 0
        protein_adherence = min(100, (self.consumed_protein / profile.target_protein) * 100) if profile.target_protein > 0 else 0
        
        # Score promedio ponderado
        score = (calorie_adherence * 0.4 + protein_adherence * 0.6)
        return round(min(100, score), 1)
    def _calculate_adherence_with_defaults(self):
        """Calcular adherencia con valores por defecto del usuario"""
        user = self.user
        target_calories = user.daily_calories or 2000
        target_protein = user.daily_protein or 150
        
        calorie_adherence = min(100, (self.consumed_calories / target_calories) * 100) if target_calories > 0 else 0
        protein_adherence = min(100, (self.consumed_protein / target_protein) * 100) if target_protein > 0 else 0
        
        score = (calorie_adherence * 0.4 + protein_adherence * 0.6)
        return round(min(100, score), 1)

class FoodConsumption(models.Model):
    """Registro individual de consumo de alimentos"""
    daily_log = models.ForeignKey(DailyNutritionLog, on_delete=models.CASCADE, related_name='food_consumptions')
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    
    # Cantidad consumida
    quantity = models.FloatField(validators=[MinValueValidator(0)], help_text="Cantidad en gramos")
    meal_type = models.CharField(max_length=20, choices=[
        ('breakfast', 'Desayuno'),
        ('lunch', 'Almuerzo'),
        ('dinner', 'Cena'),
        ('snack', 'Snack'),
    ])
    
    # Valores nutricionales calculados para esta porción
    calories_consumed = models.FloatField()
    protein_consumed = models.FloatField()
    carbs_consumed = models.FloatField()
    fat_consumed = models.FloatField()
    
    timestamp = models.DateTimeField(auto_now_add=True)
    
    def save(self, *args, **kwargs):
        """Calcular valores nutricionales basados en cantidad"""
        factor = self.quantity / self.food.serving_size
        self.calories_consumed = self.food.calories * factor
        self.protein_consumed = self.food.protein * factor
        self.carbs_consumed = self.food.carbohydrate * factor
        self.fat_consumed = self.food.fat * factor
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.food.name} - {self.quantity}g ({self.meal_type})"

class RecommendationSession(models.Model):
    """Sesión de recomendaciones para un usuario"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    session_type = models.CharField(max_length=30, choices=[
        ('daily_planning', 'Planificación diaria'),
        ('meal_suggestion', 'Sugerencia de comida'),
        ('nutrient_gap', 'Completar nutrientes'),
        ('similar_foods', 'Alimentos similares'),
    ])
    
    # Contexto de la recomendación
    current_nutrition = models.JSONField(default=dict, help_text="Estado nutricional actual")
    user_preferences = models.JSONField(default=dict, help_text="Preferencias aplicadas")
    
    # Metadatos
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_session_type_display()}"

class Recommendation(models.Model):
    """Recomendación individual de alimento"""
    session = models.ForeignKey(RecommendationSession, on_delete=models.CASCADE, related_name='recommendations')
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    
    # Scoring de la recomendación
    total_score = models.FloatField(help_text="Score total de 0-100")
    nutrition_score = models.FloatField(help_text="Score nutricional")
    preference_score = models.FloatField(help_text="Score de preferencias")
    variety_score = models.FloatField(help_text="Score de variedad")
    
    # Cantidad sugerida
    suggested_quantity = models.FloatField(help_text="Cantidad sugerida en gramos")
    
    # Razón de la recomendación
    reason = models.TextField(help_text="Por qué se recomienda este alimento")
    
    # Feedback del usuario
    user_feedback = models.CharField(max_length=20, choices=[
        ('accepted', 'Aceptado'),
        ('rejected', 'Rechazado'),
        ('modified', 'Modificado'),
        ('pending', 'Pendiente'),
    ], default='pending')
    
    position = models.IntegerField(help_text="Posición en la lista de recomendaciones")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['position']
        unique_together = ('session', 'position')
    
    def __str__(self):
        return f"{self.food.name} (Score: {self.total_score})"

class UserFoodPreference(models.Model):
    """Preferencias aprendidas automáticamente"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    food = models.ForeignKey(Food, on_delete=models.CASCADE)
    
    # Preferencia implícita calculada
    preference_score = models.FloatField(
        validators=[MinValueValidator(-1), MaxValueValidator(1)],
        help_text="Score de -1 (no le gusta) a 1 (le gusta mucho)"
    )
    
    # Factores que influyen
    frequency_consumed = models.IntegerField(default=0)
    last_consumed = models.DateTimeField(null=True, blank=True)
    average_rating = models.FloatField(null=True, blank=True)
    
    # Contexto de preferencia
    preferred_meal_types = models.JSONField(default=list, help_text="Tipos de comida donde prefiere este alimento")
    
    confidence = models.FloatField(default=0.5, help_text="Confianza en la predicción")
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('user', 'food')
    
    def __str__(self):
        return f"{self.user.username} - {self.food.name} ({self.preference_score:.2f})"

class SimilarFood(models.Model):
    """Alimentos similares nutricionales"""
    food1 = models.ForeignKey(Food, on_delete=models.CASCADE, related_name='similar_to')
    food2 = models.ForeignKey(Food, on_delete=models.CASCADE, related_name='similar_from')
    
    # Métricas de similitud
    nutritional_similarity = models.FloatField(help_text="Similitud nutricional 0-1")
    macro_similarity = models.FloatField(help_text="Similitud de macronutrientes 0-1")
    overall_similarity = models.FloatField(help_text="Similitud general 0-1")
    
    # Razón de similitud
    similarity_factors = models.JSONField(default=list, help_text="Factores que los hacen similares")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('food1', 'food2')
        indexes = [
            models.Index(fields=['food1', 'overall_similarity']),
        ]
    
    def __str__(self):
        return f"{self.food1.name} ≈ {self.food2.name} ({self.overall_similarity:.2f})"