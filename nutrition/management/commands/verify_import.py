# nutrition/management/commands/verify_import.py
from django.core.management.base import BaseCommand
from nutrition.models import Food, FoodCategory

class Command(BaseCommand):
    help = 'Verificar datos importados'

    def handle(self, *args, **options):
        # Estadísticas generales
        total_foods = Food.objects.count()
        total_categories = FoodCategory.objects.count()
        verified_foods = Food.objects.filter(is_verified=True).count()
        
        self.stdout.write('='*50)
        self.stdout.write('ESTADÍSTICAS DE IMPORTACIÓN')
        self.stdout.write('='*50)
        self.stdout.write(f'Total de alimentos: {total_foods}')
        self.stdout.write(f'Total de categorías: {total_categories}')
        self.stdout.write(f'Alimentos verificados: {verified_foods}')
        
        # Alimentos por categoría
        self.stdout.write('\nALIMENTOS POR CATEGORÍA:')
        for category in FoodCategory.objects.all():
            count = Food.objects.filter(category=category).count()
            self.stdout.write(f'  {category.name}: {count}')
        
        # Alimentos con valores nutricionales extremos
        self.stdout.write('\nALIMENTOS CON VALORES ALTOS:')
        high_protein = Food.objects.filter(protein__gte=30).count()
        high_calories = Food.objects.filter(calories__gte=500).count()
        high_fiber = Food.objects.filter(fiber__gte=10).count()
        
        self.stdout.write(f'  Alta proteína (>30g): {high_protein}')
        self.stdout.write(f'  Altas calorías (>500): {high_calories}')
        self.stdout.write(f'  Alta fibra (>10g): {high_fiber}')
        
        # Ejemplos de alimentos
        self.stdout.write('\nEJEMPLOS DE ALIMENTOS IMPORTADOS:')
        for food in Food.objects.all()[:5]:
            self.stdout.write(f'  {food.name} - {food.calories} cal, {food.protein}g proteína')