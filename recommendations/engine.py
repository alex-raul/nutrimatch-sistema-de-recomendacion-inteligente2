# recommendations/engine.py
import numpy as np
from django.db.models import Q, Avg, Count
from django.utils import timezone
from datetime import datetime, timedelta
from nutrition.models import Food
from .models import (
    UserFoodRating, UserFoodPreference, DailyNutritionLog,
    FoodConsumption, NutritionalProfile
)

class RecommendationEngine:
    """Motor principal de recomendaciones de NutriMatch"""
    
    def __init__(self, user):
        self.user = user
        self.nutritional_profile = getattr(user, 'nutritional_profile', None)
        self.user_preferences = getattr(user, 'preferences', None)
        
    def get_recommendations(self, session_type='meal_suggestion', meal_type=None, 
                          current_nutrition=None, count=10):
        """
        Obtener recomendaciones personalizadas
        
        Args:
            session_type: Tipo de sesión ('meal_suggestion', 'nutrient_gap', etc.)
            meal_type: Tipo de comida ('breakfast', 'lunch', 'dinner', 'snack')
            current_nutrition: Estado nutricional actual del día
            count: Número de recomendaciones a devolver
        """
        
        # Obtener alimentos candidatos
        candidate_foods = self._get_candidate_foods(meal_type)
        
        # Calcular scores para cada alimento
        scored_foods = []
        for food in candidate_foods:
            score_data = self._calculate_food_score(food, current_nutrition, meal_type)
            if score_data['total_score'] > 0:
                scored_foods.append(score_data)
        
        # Ordenar por score total
        scored_foods.sort(key=lambda x: x['total_score'], reverse=True)
        
        # Aplicar diversidad (evitar recomendar alimentos muy similares)
        diverse_foods = self._apply_diversity_filter(scored_foods, count * 2)
        
        # Tomar top N
        return diverse_foods[:count]
    
    def _get_candidate_foods(self, meal_type=None):
        """Obtener alimentos candidatos para recomendación"""
        foods = Food.objects.filter(is_verified=True)
        
        # Aplicar filtros de restricciones dietéticas SOLO si el usuario las tiene
        if self.user_preferences:
            if self.user_preferences.is_vegetarian:
                # Excluir carnes (esto se puede mejorar con tags específicos)
                foods = foods.exclude(
                    Q(name__icontains='chicken') | Q(name__icontains='beef') |
                    Q(name__icontains='pork') | Q(name__icontains='meat')
                )
            
            if self.user_preferences.is_vegan:
                # Excluir productos animales
                foods = foods.exclude(
                    Q(name__icontains='milk') | Q(name__icontains='cheese') |
                    Q(name__icontains='egg') | Q(name__icontains='yogurt')
                )
            
            if self.user_preferences.is_gluten_free:
                # Excluir productos con gluten
                foods = foods.exclude(
                    Q(name__icontains='bread') | Q(name__icontains='pasta') |
                    Q(name__icontains='wheat')
                )
        
        # Excluir alergias del usuario (solo si las tiene)
        user_allergens = self.user.allergies.values_list('allergen', flat=True)
        for allergen in user_allergens:
            foods = foods.exclude(name__icontains=allergen)
        
        # Filtros específicos por tipo de comida - MÁS FLEXIBLES
        if meal_type == 'breakfast':
            # Ampliar opciones de desayuno
            breakfast_foods = foods.filter(
                Q(name__icontains='egg') | Q(name__icontains='milk') |
                Q(name__icontains='oat') | Q(name__icontains='fruit') |
                Q(name__icontains='yogurt') | Q(name__icontains='cereal') |
                Q(name__icontains='banana') | Q(name__icontains='apple') |
                Q(name__icontains='orange') | Q(name__icontains='bread') |
                Q(protein__gte=10)  # Cualquier alimento con buena proteína
            )
            if breakfast_foods.exists():
                foods = breakfast_foods
        elif meal_type == 'snack':
            # Snacks saludables
            snack_foods = foods.filter(
                Q(calories__lte=300) |  # Aumentar límite de calorías
                Q(name__icontains='fruit') | Q(name__icontains='nut') |
                Q(name__icontains='yogurt')
            )
            if snack_foods.exists():
                foods = snack_foods
        
        # Si no hay suficientes alimentos después de filtros, relajar restricciones
        if foods.count() < 10:
            foods = Food.objects.filter(is_verified=True)
        
        return foods.select_related('category').order_by('?')[:200]  # Limitar para performance
    
    def _calculate_food_score(self, food, current_nutrition=None, meal_type=None):
        """Calcular score total de un alimento"""
        
        # 1. Score nutricional (40% del total)
        nutrition_score = self._calculate_nutrition_score(food, current_nutrition)
        
        # 2. Score de preferencias (30% del total)
        preference_score = self._calculate_preference_score(food, meal_type)
        
        # 3. Score de variedad (20% del total)
        variety_score = self._calculate_variety_score(food)
        
        # 4. Score de conveniencia (10% del total)
        convenience_score = self._calculate_convenience_score(food)
        
        # Pesos configurables desde el perfil nutricional
        if self.nutritional_profile:
            health_weight = self.nutritional_profile.health_importance
            taste_weight = self.nutritional_profile.taste_importance
            protein_weight = self.nutritional_profile.protein_importance
        else:
            health_weight = taste_weight = protein_weight = 1.0
        
        # Score total ponderado
        total_score = (
            nutrition_score * 0.4 * health_weight +
            preference_score * 0.3 * taste_weight +
            variety_score * 0.2 +
            convenience_score * 0.1
        )
        
        # Bonus por alta proteína si es importante para el usuario
        if food.protein >= 15:  # Alimento alto en proteína
            total_score *= (1 + 0.1 * protein_weight)
        
        return {
            'food': food,
            'total_score': round(min(100, total_score), 2),
            'nutrition_score': round(nutrition_score, 2),
            'preference_score': round(preference_score, 2),
            'variety_score': round(variety_score, 2),
            'convenience_score': round(convenience_score, 2),
            'suggested_quantity': self._calculate_suggested_quantity(food, current_nutrition),
            'reason': self._generate_recommendation_reason(food, nutrition_score, preference_score)
        }
    
    def _calculate_nutrition_score(self, food, current_nutrition=None):
        """Calcular qué tan bien satisface las necesidades nutricionales"""
        if not self.nutritional_profile:
            return 50  # Score neutral si no hay perfil
        
        score = 0
        max_score = 100
        
        # Si tenemos el estado nutricional actual, calcular qué falta
        if current_nutrition:
            remaining_calories = max(0, self.nutritional_profile.target_calories - current_nutrition.get('calories', 0))
            remaining_protein = max(0, self.nutritional_profile.target_protein - current_nutrition.get('protein', 0))
            remaining_carbs = max(0, self.nutritional_profile.target_carbs - current_nutrition.get('carbs', 0))
            remaining_fat = max(0, self.nutritional_profile.target_fat - current_nutrition.get('fat', 0))
        else:
            # Usar objetivos completos
            remaining_calories = self.nutritional_profile.target_calories
            remaining_protein = self.nutritional_profile.target_protein
            remaining_carbs = self.nutritional_profile.target_carbs
            remaining_fat = self.nutritional_profile.target_fat
        
        # Score basado en densidad nutricional
        if food.calories > 0:
            protein_density = (food.protein / food.calories) * 100
            fiber_content = food.fiber
            
            # Bonus por alta densidad proteica
            if protein_density >= 15:
                score += 25
            elif protein_density >= 10:
                score += 15
            elif protein_density >= 5:
                score += 10
            
            # Bonus por contenido de fibra
            if fiber_content >= 5:
                score += 20
            elif fiber_content >= 3:
                score += 10
            
            # Penalizar exceso de sodio
            if food.sodium > 400:  # mg por porción
                score -= 15
            elif food.sodium > 200:
                score -= 5
            
            # Bonus por micronutrientes importantes
            if food.vitamin_c > 10:
                score += 5
            if food.calcium > 100:
                score += 5
            if food.iron > 2:
                score += 5
        
        # Ajustar según necesidades específicas del usuario
        if remaining_protein > 20 and food.protein >= 15:
            score += 20  # Bonus si necesita mucha proteína
        
        if remaining_calories < 300 and food.calories > 400:
            score -= 20  # Penalizar si quedan pocas calorías pero el alimento es muy calórico
        
        return max(0, min(max_score, score))
    
    def _calculate_preference_score(self, food, meal_type=None):
        """Calcular score basado en preferencias del usuario"""
        score = 50  # Score neutral base
        
        # Buscar calificación directa del usuario
        try:
            rating = UserFoodRating.objects.get(user=self.user, food=food)
            score = rating.rating * 20  # Convertir 1-5 a 20-100
            
            # Bonus si ha calificado positivamente en este tipo de comida
            if meal_type and rating.meal_type == meal_type and rating.rating >= 4:
                score += 10
                
        except UserFoodRating.DoesNotExist:
            # Buscar preferencia aprendida
            try:
                preference = UserFoodPreference.objects.get(user=self.user, food=food)
                score = 50 + (preference.preference_score * 50)  # Convertir -1,1 a 0-100
                
                # Ajustar por confianza
                score = 50 + (score - 50) * preference.confidence
                
            except UserFoodPreference.DoesNotExist:
                # Buscar patrones en alimentos similares de la misma categoría
                if food.category:
                    avg_rating = UserFoodRating.objects.filter(
                        user=self.user,
                        food__category=food.category
                    ).aggregate(avg_rating=Avg('rating'))['avg_rating']
                    
                    if avg_rating:
                        score = avg_rating * 20
        
        return max(0, min(100, score))
    
    def _calculate_variety_score(self, food):
        """Calcular score de variedad (evitar monotonía)"""
        # Verificar cuándo fue la última vez que consumió este alimento
        last_consumption = FoodConsumption.objects.filter(
            daily_log__user=self.user,
            food=food
        ).order_by('-timestamp').first()
        
        if not last_consumption:
            return 100  # Máximo score si nunca lo ha consumido
        
        days_since = (timezone.now().date() - last_consumption.daily_log.date).days
        
        if days_since >= 7:
            return 100
        elif days_since >= 3:
            return 70
        elif days_since >= 1:
            return 40
        else:
            return 10  # Penalizar si lo consumió hoy
    
    def _calculate_convenience_score(self, food):
        """Calcular score de conveniencia (tiempo de preparación, disponibilidad)"""
        score = 70  # Score base
        
        # Preferir alimentos más simples/naturales
        if any(word in food.name.lower() for word in ['fresh', 'raw', 'natural']):
            score += 20
        
        # Penalizar alimentos muy procesados
        if any(word in food.name.lower() for word in ['processed', 'instant', 'frozen']):
            score -= 10
        
        return max(0, min(100, score))
    
    def _calculate_suggested_quantity(self, food, current_nutrition=None):
        """Calcular cantidad sugerida del alimento"""
        if not self.nutritional_profile:
            return food.serving_size  # Porción estándar
        
        # Calcular basado en necesidades restantes
        if current_nutrition:
            remaining_calories = max(0, self.nutritional_profile.target_calories - current_nutrition.get('calories', 0))
        else:
            remaining_calories = self.nutritional_profile.target_calories * 0.3  # 30% de las calorías diarias
        
        if food.calories > 0:
            # Calcular cantidad para no exceder calorías restantes
            max_quantity_by_calories = (remaining_calories / food.calories) * food.serving_size
            
            # Limitar entre 50g y 300g para ser práctico
            suggested_quantity = max(50, min(300, max_quantity_by_calories))
        else:
            suggested_quantity = food.serving_size
        
        return round(suggested_quantity)
    
    def _generate_recommendation_reason(self, food, nutrition_score, preference_score):
        """Generar razón textual de por qué se recomienda este alimento"""
        reasons = []
        
        if nutrition_score >= 80:
            if food.protein >= 15:
                reasons.append("excelente fuente de proteína")
            if food.fiber >= 5:
                reasons.append("alto contenido de fibra")
            if food.vitamin_c > 10:
                reasons.append("rico en vitamina C")
        
        if preference_score >= 80:
            reasons.append("alimento que sueles disfrutar")
        elif preference_score >= 60:
            reasons.append("buena opción basada en tus preferencias")
        
        if food.calories <= 100:
            reasons.append("bajo en calorías")
        
        if not reasons:
            reasons.append("opción balanceada para tu objetivo")
        
        return f"Recomendado porque es {' y '.join(reasons)}."
    
    def _apply_diversity_filter(self, scored_foods, max_count):
        """Aplicar filtro de diversidad para evitar alimentos muy similares"""
        if len(scored_foods) <= max_count:
            return scored_foods
        
        diverse_foods = []
        used_categories = set()
        
        # Primera pasada: un alimento por categoría (top scored)
        for food_data in scored_foods:
            category = food_data['food'].category
            if category and category not in used_categories:
                diverse_foods.append(food_data)
                used_categories.add(category)
                
                if len(diverse_foods) >= max_count:
                    break
        
        # Segunda pasada: llenar espacios restantes
        if len(diverse_foods) < max_count:
            for food_data in scored_foods:
                if food_data not in diverse_foods:
                    diverse_foods.append(food_data)
                    if len(diverse_foods) >= max_count:
                        break
        
        return diverse_foods

    def learn_from_consumption(self, food_consumption):
        """Aprender de los patrones de consumo del usuario"""
        food = food_consumption.food
        meal_type = food_consumption.meal_type
        
        # Actualizar o crear preferencia
        preference, created = UserFoodPreference.objects.get_or_create(
            user=self.user,
            food=food,
            defaults={
                'preference_score': 0.1,  # Preferencia ligeramente positiva por consumir
                'frequency_consumed': 1,
                'confidence': 0.3
            }
        )
        
        if not created:
            # Incrementar frecuencia y ajustar preferencia
            preference.frequency_consumed += 1
            preference.preference_score = min(1.0, preference.preference_score + 0.05)
            preference.confidence = min(1.0, preference.confidence + 0.1)
            
            # Actualizar tipos de comida preferidos
            preferred_meals = preference.preferred_meal_types or []
            if meal_type not in preferred_meals:
                preferred_meals.append(meal_type)
                preference.preferred_meal_types = preferred_meals
        
        preference.last_consumed = timezone.now()
        preference.save()