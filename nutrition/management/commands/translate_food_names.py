# nutrition/management/commands/translate_food_names.py
import pandas as pd
from django.core.management.base import BaseCommand
from nutrition.models import Food

class Command(BaseCommand):
    help = 'Traducir nombres de alimentos al español'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--translation-file',
            type=str,
            help='Archivo CSV con traducciones (columnas: english, spanish)'
        )
        parser.add_argument(
            '--auto-translate',
            action='store_true',
            help='Traducir automáticamente usando reglas básicas'
        )

    def handle(self, *args, **options):
        if options['translation_file']:
            self.translate_from_file(options['translation_file'])
        elif options['auto_translate']:
            self.auto_translate()
        else:
            self.stdout.write(
                self.style.ERROR('Debes especificar --translation-file o --auto-translate')
            )

    def translate_from_file(self, file_path):
        """Traducir usando archivo de traducciones"""
        try:
            df = pd.read_csv(file_path)
            translations = dict(zip(df['english'], df['spanish']))
            
            updated = 0
            for food in Food.objects.filter(name_es__isnull=True):
                if food.name in translations:
                    food.name_es = translations[food.name]
                    food.save()
                    updated += 1
            
            self.stdout.write(
                self.style.SUCCESS(f'Actualizados {updated} nombres en español')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )

    def auto_translate(self):
        """Traducción automática básica"""
        basic_translations = {
            'chicken': 'pollo',
            'beef': 'carne de res',
            'pork': 'cerdo',
            'fish': 'pescado',
            'salmon': 'salmón',
            'tuna': 'atún',
            'milk': 'leche',
            'cheese': 'queso',
            'yogurt': 'yogur',
            'apple': 'manzana',
            'banana': 'plátano',
            'orange': 'naranja',
            'rice': 'arroz',
            'bread': 'pan',
            'pasta': 'pasta',
            'beans': 'frijoles',
            'oil': 'aceite',
            'butter': 'mantequilla',
            'egg': 'huevo',
            'potato': 'papa',
            'tomato': 'tomate',
            'carrot': 'zanahoria',
            'onion': 'cebolla',
            'lettuce': 'lechuga',
            'spinach': 'espinacas',
        }
        
        updated = 0
        for food in Food.objects.filter(name_es__isnull=True):
            food_name_lower = food.name.lower()
            translated = False
            
            for eng, esp in basic_translations.items():
                if eng in food_name_lower:
                    food.name_es = food.name.lower().replace(eng, esp).title()
                    food.save()
                    updated += 1
                    translated = True
                    break
            
            if not translated:
                # Mantener nombre original si no se puede traducir
                food.name_es = food.name
                food.save()
                updated += 1
        
        self.stdout.write(
            self.style.SUCCESS(f'Procesados {updated} nombres')
        )