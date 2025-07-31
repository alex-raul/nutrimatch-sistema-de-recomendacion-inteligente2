# nutrition/services.py
import requests
from django.conf import settings
from decouple import config
import time

class USDAFoodDataService:
    """Servicio para interactuar con USDA FoodData Central API"""
    
    def __init__(self):
        self.api_key = config('USDA_API_KEY', default='')
        self.base_url = 'https://api.nal.usda.gov/fdc/v1'
        
    def search_foods(self, query, max_results=20):
        """Buscar alimentos en la API del USDA"""
        if not self.api_key:
            return {'error': 'API key no configurada'}
            
        url = f"{self.base_url}/foods/search"
        params = {
            'query': query,
            'pageSize': max_results,
            'api_key': self.api_key,
            'dataType': ['Foundation', 'SR Legacy'],  # Datos más confiables
            'sortBy': 'dataType.keyword',
            'sortOrder': 'asc'
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': f'Error de conexión: {str(e)}'}
    
    def get_food_details(self, fdc_id):
        """Obtener detalles completos de un alimento por FDC ID"""
        if not self.api_key:
            return {'error': 'API key no configurada'}
            
        url = f"{self.base_url}/food/{fdc_id}"
        params = {
            'api_key': self.api_key,
            'nutrients': [203, 204, 205, 208, 291, 269, 307, 301, 303]  # Macros principales
        }
        
        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            return {'error': f'Error de conexión: {str(e)}'}
    
    def import_food_from_usda(self, fdc_id):
        """Importar un alimento desde USDA a nuestra base de datos"""
        from .models import Food, FoodCategory
        
        # Obtener datos del USDA
        usda_data = self.get_food_details(fdc_id)
        if 'error' in usda_data:
            return usda_data
        
        try:
            # Extraer información básica
            name = usda_data.get('description', 'Unknown Food')
            brand_owner = usda_data.get('brandOwner', '')
            if brand_owner:
                name = f"{name} ({brand_owner})"
            
            # Extraer nutrientes
            nutrients = {}
            for nutrient in usda_data.get('foodNutrients', []):
                nutrient_id = nutrient.get('nutrient', {}).get('id')
                amount = nutrient.get('amount', 0)
                
                # Mapeo de IDs de nutrientes del USDA
                nutrient_mapping = {
                    208: 'calories',      # Energy
                    203: 'protein',       # Protein
                    205: 'carbohydrate',  # Carbohydrate
                    204: 'fat',           # Total lipid (fat)
                    291: 'fiber',         # Fiber, total dietary
                    269: 'sugars',        # Sugars, total
                    307: 'sodium',        # Sodium
                    301: 'calcium',       # Calcium
                    303: 'iron',          # Iron
                }
                
                if nutrient_id in nutrient_mapping:
                    nutrients[nutrient_mapping[nutrient_id]] = amount or 0
            
            # Crear categoría si no existe
            food_category = usda_data.get('foodCategory', {}).get('description', 'Imported from USDA')
            category, created = FoodCategory.objects.get_or_create(
                name=food_category,
                defaults={'name_es': food_category}
            )
            
            # Crear alimento en nuestra BD
            food, created = Food.objects.get_or_create(
                usda_fdc_id=str(fdc_id),
                defaults={
                    'name': name,
                    'name_es': name,  # Por ahora sin traducir
                    'category': category,
                    'serving_size': 100,  # USDA usa 100g como estándar
                    'calories': nutrients.get('calories', 0),
                    'protein': nutrients.get('protein', 0),
                    'carbohydrate': nutrients.get('carbohydrate', 0),
                    'fat': nutrients.get('fat', 0),
                    'fiber': nutrients.get('fiber', 0),
                    'sugars': nutrients.get('sugars', 0),
                    'sodium': nutrients.get('sodium', 0),
                    'calcium': nutrients.get('calcium', 0),
                    'iron': nutrients.get('iron', 0),
                    'data_source': 'usda_api',
                    'is_verified': True
                }
            )
            
            return {
                'success': True,
                'food': food,
                'created': created,
                'message': f"Alimento {'creado' if created else 'actualizado'} desde USDA"
            }
            
        except Exception as e:
            return {'error': f'Error procesando datos: {str(e)}'}