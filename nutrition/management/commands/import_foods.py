# nutrition/management/commands/import_foods.py
import pandas as pd
import os
from django.core.management.base import BaseCommand
from django.db import transaction
from nutrition.models import Food, FoodCategory

class Command(BaseCommand):
    help = 'Importar alimentos desde archivo CSV'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'csv_file',
            type=str,
            help='Ruta al archivo CSV con los datos nutricionales'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Tamaño del lote para inserción en BD (default: 100)'
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Saltar alimentos que ya existen en la BD'
        )
        parser.add_argument(
            '--create-categories',
            action='store_true',
            help='Crear categorías automáticamente basadas en nombres'
        )

    def handle(self, *args, **options):
        csv_file = options['csv_file']
        batch_size = options['batch_size']
        skip_existing = options['skip_existing']
        create_categories = options['create_categories']
        
        # Verificar que el archivo existe
        if not os.path.exists(csv_file):
            self.stdout.write(
                self.style.ERROR(f'Archivo no encontrado: {csv_file}')
            )
            return
        
        try:
            # Leer CSV
            self.stdout.write('Leyendo archivo CSV...')
            df = pd.read_csv(csv_file)
            
            # Mostrar información del dataset
            self.stdout.write(f'Archivo cargado: {len(df)} filas, {len(df.columns)} columnas')
            self.stdout.write('Columnas encontradas:')
            for col in df.columns:
                self.stdout.write(f'  - {col}')
            
            # Verificar columnas requeridas
            required_columns = ['name', 'calories', 'protein', 'carbohydrate', 'fat']
            missing_columns = [col for col in required_columns if col not in df.columns]
            
            if missing_columns:
                self.stdout.write(
                    self.style.ERROR(f'Columnas faltantes: {missing_columns}')
                )
                return
            
            # Limpiar datos
            df = self.clean_data(df)
            
            # Crear categorías si se solicita
            if create_categories:
                self.create_food_categories(df)
            
            # Importar alimentos
            self.import_foods(df, batch_size, skip_existing)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error durante la importación: {str(e)}')
            )
            raise

    def clean_data(self, df):
        """Limpiar y preparar datos"""
        self.stdout.write('Limpiando datos...')
        
        # Reemplazar valores nulos con 0 para campos numéricos
        numeric_columns = df.select_dtypes(include=['number']).columns
        df[numeric_columns] = df[numeric_columns].fillna(0)
        
        # Limpiar nombres
        if 'name' in df.columns:
            df['name'] = df['name'].str.strip()
            df['name'] = df['name'].str.replace(r'\s+', ' ', regex=True)
        
        # Asegurar que serving_size existe
        if 'serving_size' not in df.columns:
            df['serving_size'] = 100  # Default 100g
        
        # Corregir nombres de columnas si es necesario
        column_corrections = {
            'irom': 'iron',
            'zink': 'zinc',
            'phosphorous': 'phosphorus'
        }
        
        for old_name, new_name in column_corrections.items():
            if old_name in df.columns:
                df = df.rename(columns={old_name: new_name})
                self.stdout.write(f'Corregido: {old_name} → {new_name}')
        
        self.stdout.write(f'Datos limpiados: {len(df)} filas válidas')
        return df

    def create_food_categories(self, df):
        """Crear categorías basadas en nombres de alimentos"""
        self.stdout.write('Creando categorías de alimentos...')
        
        # Diccionario de categorías basado en palabras clave
        category_keywords = {
            'Carnes': ['chicken', 'beef', 'pork', 'lamb', 'turkey', 'meat', 'pollo', 'carne', 'cerdo'],
            'Pescados y Mariscos': ['fish', 'salmon', 'tuna', 'shrimp', 'crab', 'pescado', 'atún', 'salmón'],
            'Lácteos': ['milk', 'cheese', 'yogurt', 'dairy', 'leche', 'queso', 'yogur'],
            'Frutas': ['apple', 'banana', 'orange', 'berry', 'fruit', 'manzana', 'plátano', 'fruta'],
            'Vegetales': ['vegetable', 'lettuce', 'tomato', 'carrot', 'spinach', 'verdura', 'lechuga'],
            'Granos': ['rice', 'bread', 'pasta', 'oats', 'wheat', 'arroz', 'pan', 'avena'],
            'Legumbres': ['beans', 'lentils', 'peas', 'legume', 'frijoles', 'lentejas'],
            'Nueces y Semillas': ['nuts', 'seeds', 'almond', 'walnut', 'nueces', 'semillas'],
            'Aceites y Grasas': ['oil', 'butter', 'fat', 'aceite', 'mantequilla'],
            'Bebidas': ['juice', 'drink', 'beverage', 'soda', 'jugo', 'bebida'],
            'Procesados': ['processed', 'snack', 'cookie', 'cake', 'galleta', 'pastel']
        }
        
        categories_created = 0
        for category_name, keywords in category_keywords.items():
            category, created = FoodCategory.objects.get_or_create(
                name=category_name,
                defaults={
                    'name_es': category_name,
                    'description': f'Categoría para {category_name.lower()}'
                }
            )
            if created:
                categories_created += 1
        
        # Crear categoría por defecto
        default_category, created = FoodCategory.objects.get_or_create(
            name='Otros',
            defaults={
                'name_es': 'Otros',
                'description': 'Alimentos sin categoría específica'
            }
        )
        if created:
            categories_created += 1
        
        self.stdout.write(f'Categorías creadas: {categories_created}')

    def get_food_category(self, food_name):
        """Determinar categoría de un alimento basado en su nombre"""
        food_name_lower = food_name.lower()
        
        category_keywords = {
            'Carnes': ['chicken', 'beef', 'pork', 'lamb', 'turkey', 'meat', 'pollo', 'carne'],
            'Pescados y Mariscos': ['fish', 'salmon', 'tuna', 'shrimp', 'pescado', 'atún'],
            'Lácteos': ['milk', 'cheese', 'yogurt', 'dairy', 'leche', 'queso'],
            'Frutas': ['apple', 'banana', 'orange', 'berry', 'fruit', 'manzana', 'fruta'],
            'Vegetales': ['vegetable', 'lettuce', 'tomato', 'carrot', 'spinach', 'verdura'],
            'Granos': ['rice', 'bread', 'pasta', 'oats', 'wheat', 'arroz', 'pan'],
            'Legumbres': ['beans', 'lentils', 'peas', 'frijoles', 'lentejas'],
            'Nueces y Semillas': ['nuts', 'seeds', 'almond', 'nueces', 'semillas'],
            'Aceites y Grasas': ['oil', 'butter', 'fat', 'aceite', 'mantequilla'],
            'Bebidas': ['juice', 'drink', 'beverage', 'jugo', 'bebida'],
        }
        
        for category_name, keywords in category_keywords.items():
            if any(keyword in food_name_lower for keyword in keywords):
                try:
                    return FoodCategory.objects.get(name=category_name)
                except FoodCategory.DoesNotExist:
                    pass
        
        # Categoría por defecto
        return FoodCategory.objects.get_or_create(name='Otros')[0]

    def import_foods(self, df, batch_size, skip_existing):
        """Importar alimentos en lotes"""
        self.stdout.write('Iniciando importación de alimentos...')
        
        total_foods = len(df)
        imported = 0
        skipped = 0
        errors = 0
        
        # Mapeo de columnas del CSV a campos del modelo
        column_mapping = {
            'name': 'name',
            'serving_size': 'serving_size',
            'calories': 'calories',
            'protein': 'protein',
            'carbohydrate': 'carbohydrate',
            'fat': 'fat',
            'fiber': 'fiber',
            'sugars': 'sugars',
            'total_fat': 'total_fat',
            'saturated_fat': 'saturated_fat',
            'monounsaturated_fatty_acids': 'monounsaturated_fat',
            'polyunsaturated_fatty_acids': 'polyunsaturated_fat',
            'fatty_acids_total_trans': 'trans_fat',
            'cholesterol': 'cholesterol',
            'sodium': 'sodium',
            'potassium': 'potassium',
            'calcium': 'calcium',
            'iron': 'iron',
            'magnesium': 'magnesium',
            'phosphorus': 'phosphorus',
            'zinc': 'zinc',
            'vitamin_a': 'vitamin_a',
            'vitamin_c': 'vitamin_c',
            'vitamin_d': 'vitamin_d',
            'vitamin_e': 'vitamin_e',
            'vitamin_k': 'vitamin_k',
            'thiamin': 'thiamin',
            'riboflavin': 'riboflavin',
            'niacin': 'niacin',
            'vitamin_b6': 'vitamin_b6',
            'vitamin_b12': 'vitamin_b12',
            'folate': 'folate',
        }
        
        foods_to_create = []
        
        for index, row in df.iterrows():
            try:
                food_name = row['name']
                
                # Verificar si ya existe
                if skip_existing and Food.objects.filter(name=food_name).exists():
                    skipped += 1
                    continue
                
                # Preparar datos del alimento
                food_data = {'name': food_name}
                
                # Mapear columnas
                for csv_col, model_field in column_mapping.items():
                    if csv_col in row and pd.notna(row[csv_col]):
                        food_data[model_field] = float(row[csv_col]) if csv_col != 'name' else str(row[csv_col])
                
                # Asignar categoría
                food_data['category'] = self.get_food_category(food_name)
                food_data['data_source'] = 'csv_import'
                
                # Crear objeto Food
                food = Food(**food_data)
                foods_to_create.append(food)
                
                # Insertar en lotes
                if len(foods_to_create) >= batch_size:
                    with transaction.atomic():
                        Food.objects.bulk_create(foods_to_create, ignore_conflicts=True)
                    imported += len(foods_to_create)
                    foods_to_create = []
                    
                    # Mostrar progreso
                    progress = (imported / total_foods) * 100
                    self.stdout.write(f'Progreso: {imported}/{total_foods} ({progress:.1f}%)')
                
            except Exception as e:
                errors += 1
                self.stdout.write(
                    self.style.WARNING(f'Error en fila {index}: {str(e)}')
                )
        
        # Insertar último lote
        if foods_to_create:
            with transaction.atomic():
                Food.objects.bulk_create(foods_to_create, ignore_conflicts=True)
            imported += len(foods_to_create)
        
        # Resumen final
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.SUCCESS('IMPORTACIÓN COMPLETADA'))
        self.stdout.write(f'Total de filas procesadas: {total_foods}')
        self.stdout.write(f'Alimentos importados: {imported}')
        self.stdout.write(f'Alimentos omitidos: {skipped}')
        self.stdout.write(f'Errores: {errors}')
        self.stdout.write('='*50)