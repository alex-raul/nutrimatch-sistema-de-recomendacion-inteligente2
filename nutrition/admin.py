# nutrition/admin.py
from django.contrib import admin
from django.utils.html import format_html
from .models import Food, FoodCategory, FoodAlias

@admin.register(FoodCategory)
class FoodCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'name_es', 'color_preview', 'food_count')
    search_fields = ('name', 'name_es')
    
    def color_preview(self, obj):
        return format_html(
            '<span style="background-color: {}; padding: 5px 10px; color: white; border-radius: 3px;">{}</span>',
            obj.color,
            obj.color
        )
    color_preview.short_description = 'Color'
    
    def food_count(self, obj):
        return obj.food_set.count()
    food_count.short_description = 'Cantidad de Alimentos'

@admin.register(Food)
class FoodAdmin(admin.ModelAdmin):
    list_display = ('name_display', 'category', 'calories', 'protein', 'carbohydrate', 'fat', 'protein_density', 'is_verified')
    list_filter = ('category', 'is_verified', 'data_source')
    search_fields = ('name', 'name_es', 'usda_fdc_id')
    autocomplete_fields = ['category']
    
    # Campos de solo lectura
    readonly_fields = ('protein_density', 'nutrient_density_score', 'created_at', 'updated_at')
    
    # Filtros en la barra lateral
    list_per_page = 25
    
    # Organización de campos
    fieldsets = (
        ('Información Básica', {
            'fields': ('name', 'name_es', 'category', 'serving_size')
        }),
        ('Macronutrientes', {
            'fields': ('calories', 'protein', 'carbohydrate', 'fat', 'fiber', 'sugars'),
            'classes': ('wide',)
        }),
        ('Grasas Detalladas', {
            'fields': ('total_fat', 'saturated_fat', 'monounsaturated_fat', 'polyunsaturated_fat', 'trans_fat', 'cholesterol'),
            'classes': ('collapse',)
        }),
        ('Minerales', {
            'fields': ('sodium', 'potassium', 'calcium', 'iron', 'magnesium', 'phosphorus', 'zinc'),
            'classes': ('collapse',)
        }),
        ('Vitaminas', {
            'fields': ('vitamin_a', 'vitamin_c', 'vitamin_d', 'vitamin_e', 'vitamin_k', 
                      'thiamin', 'riboflavin', 'niacin', 'vitamin_b6', 'vitamin_b12', 'folate'),
            'classes': ('collapse',)
        }),
        ('Métricas Calculadas', {
            'fields': ('protein_density', 'nutrient_density_score'),
            'classes': ('collapse',)
        }),
        ('Control de Calidad', {
            'fields': ('is_verified', 'usda_fdc_id', 'data_source'),
            'classes': ('collapse',)
        }),
        ('Metadatos', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    # Acciones personalizadas
    actions = ['mark_as_verified', 'recalculate_metrics', 'export_selected_foods']
    
    def name_display(self, obj):
        return obj.name_es or obj.name
    name_display.short_description = 'Nombre'
    name_display.admin_order_field = 'name_es'
    
    def mark_as_verified(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} alimentos marcados como verificados.')
    mark_as_verified.short_description = "Marcar como verificados"
    
    def recalculate_metrics(self, request, queryset):
        updated = 0
        for food in queryset:
            food.save()  # Esto ejecutará el cálculo automático
            updated += 1
        self.message_user(request, f'Métricas recalculadas para {updated} alimentos.')
    recalculate_metrics.short_description = "Recalcular métricas"

@admin.register(FoodAlias)
class FoodAliasAdmin(admin.ModelAdmin):
    list_display = ('alias', 'food', 'language')
    list_filter = ('language',)
    search_fields = ('alias', 'food__name', 'food__name_es')
    autocomplete_fields = ['food']