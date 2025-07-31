# recommendations/management/commands/create_sample_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import random
from nutrition.models import Food
from recommendations.models import DailyNutritionLog, FoodConsumption, UserFoodRating

User = get_user_model()

class Command(BaseCommand):
    help = 'Crear datos de prueba para el sistema de recomendaciones'

    def add_arguments(self, parser):
        parser.add_argument('--username', type=str, help='Usuario para crear datos de prueba')

    def handle(self, *args, **options):
        username = options.get('username')
        if not username:
            self.stdout.write(self.style.ERROR('Debes especificar --username'))
            return

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Usuario {username} no encontrado'))
            return

        # Crear logs de los últimos 7 días
        foods = list(Food.objects.all()[:50])  # Primeros 50 alimentos
        meal_types = ['breakfast', 'lunch', 'dinner', 'snack']
        
        for i in range(7):
            date = timezone.now().date() - timedelta(days=i)
            
            daily_log, created = DailyNutritionLog.objects.get_or_create(
                user=user, date=date
            )
            
            # Crear consumos aleatorios
            daily_calories = 0
            daily_protein = 0
            daily_carbs = 0
            daily_fat = 0
            
            for meal_type in meal_types:
                # 1-3 alimentos por comida
                for _ in range(random.randint(1, 3)):
                    food = random.choice(foods)
                    quantity = random.randint(50, 200)
                    
                    consumption = FoodConsumption.objects.create(
                        daily_log=daily_log,
                        food=food,
                        quantity=quantity,
                        meal_type=meal_type
                    )
                    
                    daily_calories += consumption.calories_consumed
                    daily_protein += consumption.protein_consumed
                    daily_carbs += consumption.carbs_consumed
                    daily_fat += consumption.fat_consumed
            
            # Actualizar totales
            daily_log.consumed_calories = daily_calories
            daily_log.consumed_protein = daily_protein
            daily_log.consumed_carbs = daily_carbs
            daily_log.consumed_fat = daily_fat
            daily_log.adherence_score = daily_log.calculate_adherence_score()
            daily_log.save()
        
        # Crear algunas calificaciones aleatorias
        for _ in range(20):
            food = random.choice(foods)
            rating = random.randint(3, 5)  # Calificaciones positivas
            
            UserFoodRating.objects.get_or_create(
                user=user,
                food=food,
                defaults={
                    'rating': rating,
                    'meal_type': random.choice(meal_types),
                    'notes': f'Calificación de prueba: {rating} estrellas'
                }
            )
        
        self.stdout.write(
            self.style.SUCCESS(f'Datos de prueba creados para {username}')
        )