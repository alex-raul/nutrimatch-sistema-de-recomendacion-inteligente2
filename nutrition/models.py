# nutrition/models.py
from django.db import models
from django.core.validators import MinValueValidator

class FoodCategory(models.Model):
    """Categorías de alimentos"""
    name = models.CharField(max_length=100, unique=True)
    name_es = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff')  # Color hex para UI
    
    class Meta:
        verbose_name_plural = "Food Categories"
    
    def __str__(self):
        return self.name_es or self.name

class Food(models.Model):
    """Modelo principal de alimentos"""
    
    # Información básica
    name = models.CharField(max_length=200, db_index=True)
    name_es = models.CharField(max_length=200, null=True, blank=True, db_index=True)
    category = models.ForeignKey(FoodCategory, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Información de porción
    serving_size = models.IntegerField(default=100, help_text="Tamaño de porción en gramos")
    
    # Macronutrientes principales
    calories = models.FloatField(validators=[MinValueValidator(0)])
    protein = models.FloatField(validators=[MinValueValidator(0)])
    carbohydrate = models.FloatField(validators=[MinValueValidator(0)])
    fat = models.FloatField(validators=[MinValueValidator(0)])
    fiber = models.FloatField(validators=[MinValueValidator(0)], default=0)
    sugars = models.FloatField(validators=[MinValueValidator(0)], default=0)
    
    # Grasas detalladas
    total_fat = models.FloatField(validators=[MinValueValidator(0)], default=0)
    saturated_fat = models.FloatField(validators=[MinValueValidator(0)], default=0)
    monounsaturated_fat = models.FloatField(validators=[MinValueValidator(0)], default=0)
    polyunsaturated_fat = models.FloatField(validators=[MinValueValidator(0)], default=0)
    trans_fat = models.FloatField(validators=[MinValueValidator(0)], default=0)
    cholesterol = models.FloatField(validators=[MinValueValidator(0)], default=0)
    
    # Minerales importantes
    sodium = models.FloatField(validators=[MinValueValidator(0)], default=0)
    potassium = models.FloatField(validators=[MinValueValidator(0)], default=0)
    calcium = models.FloatField(validators=[MinValueValidator(0)], default=0)
    iron = models.FloatField(validators=[MinValueValidator(0)], default=0)
    magnesium = models.FloatField(validators=[MinValueValidator(0)], default=0)
    phosphorus = models.FloatField(validators=[MinValueValidator(0)], default=0)
    zinc = models.FloatField(validators=[MinValueValidator(0)], default=0)
    
    # Vitaminas principales
    vitamin_a = models.FloatField(validators=[MinValueValidator(0)], default=0)
    vitamin_c = models.FloatField(validators=[MinValueValidator(0)], default=0)
    vitamin_d = models.FloatField(validators=[MinValueValidator(0)], default=0)
    vitamin_e = models.FloatField(validators=[MinValueValidator(0)], default=0)
    vitamin_k = models.FloatField(validators=[MinValueValidator(0)], default=0)
    thiamin = models.FloatField(validators=[MinValueValidator(0)], default=0)
    riboflavin = models.FloatField(validators=[MinValueValidator(0)], default=0)
    niacin = models.FloatField(validators=[MinValueValidator(0)], default=0)
    vitamin_b6 = models.FloatField(validators=[MinValueValidator(0)], default=0)
    vitamin_b12 = models.FloatField(validators=[MinValueValidator(0)], default=0)
    folate = models.FloatField(validators=[MinValueValidator(0)], default=0)
    
    # Campos calculados para recomendaciones
    protein_density = models.FloatField(null=True, blank=True)  # proteína por caloría
    nutrient_density_score = models.FloatField(null=True, blank=True)
    
    # Control de calidad y origen
    is_verified = models.BooleanField(default=False)
    usda_fdc_id = models.CharField(max_length=20, null=True, blank=True, unique=True)
    data_source = models.CharField(max_length=50, default='local')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['name_es']),
            models.Index(fields=['calories']),
            models.Index(fields=['protein']),
        ]
    
    def __str__(self):
        return self.name_es or self.name
    
    def calculate_protein_density(self):
        """Calcular densidad proteica (g proteína por 100 calorías)"""
        if self.calories > 0:
            return round((self.protein / self.calories) * 100, 2)
        return 0
    
    def calculate_nutrient_density(self):
        """Calcular score de densidad nutricional"""
        if self.calories == 0:
            return 0
            
        # Factores importantes para el score
        vitamin_score = (self.vitamin_a + self.vitamin_c + self.vitamin_d + 
                        self.vitamin_e + self.folate) / 5
        mineral_score = (self.calcium + self.iron + self.magnesium + 
                        self.potassium + self.zinc) / 5
        
        # Score basado en nutrientes por caloría
        nutrient_score = (vitamin_score + mineral_score + self.fiber) / self.calories * 1000
        return round(nutrient_score, 2)
    
    def save(self, *args, **kwargs):
        """Override save para calcular campos automáticamente"""
        self.protein_density = self.calculate_protein_density()
        self.nutrient_density_score = self.calculate_nutrient_density()
        super().save(*args, **kwargs)

class FoodAlias(models.Model):
    """Nombres alternativos para alimentos"""
    food = models.ForeignKey(Food, on_delete=models.CASCADE, related_name='aliases')
    alias = models.CharField(max_length=200, db_index=True)
    language = models.CharField(max_length=5, default='es')
    
    class Meta:
        unique_together = ('food', 'alias')
    
    def __str__(self):
        return f"{self.alias} -> {self.food.name}"

class Meta:
    verbose_name = "Alimento"
    verbose_name_plural = "Alimentos"
    indexes = [
        models.Index(fields=['name']),
        models.Index(fields=['name_es']),
        models.Index(fields=['calories']),
        models.Index(fields=['protein']),
    ]
