# users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, UserAllergy, UserPreference

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin personalizado para CustomUser"""
    
    # Campos que se muestran en la lista
    list_display = ('username', 'email', 'first_name', 'last_name', 'age', 'goal', 'activity_level', 'profile_completed', 'date_joined')
    list_filter = ('goal', 'activity_level', 'gender', 'profile_completed', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    
    # Organización de campos en el formulario
    fieldsets = UserAdmin.fieldsets + (
        ('Información Personal Adicional', {
            'fields': ('age', 'weight', 'height', 'gender')
        }),
        ('Objetivos y Actividad', {
            'fields': ('goal', 'activity_level', 'profile_completed')
        }),
        ('Necesidades Nutricionales', {
            'fields': ('daily_calories', 'daily_protein', 'daily_carbs', 'daily_fat'),
            'classes': ('collapse',)  # Sección colapsable
        }),
    )
    
    # Campos de solo lectura (calculados automáticamente)
    readonly_fields = ('date_joined', 'last_login')
    
    # Acciones personalizadas
    actions = ['calculate_nutrition_needs']
    
    def calculate_nutrition_needs(self, request, queryset):
        """Acción para recalcular necesidades nutricionales"""
        updated = 0
        for user in queryset:
            if user.weight and user.height and user.age:
                user.daily_calories = user.calculate_daily_calories()
                user.save()
                updated += 1
        
        self.message_user(request, f'Necesidades nutricionales actualizadas para {updated} usuarios.')
    calculate_nutrition_needs.short_description = "Recalcular necesidades nutricionales"

@admin.register(UserAllergy)
class UserAllergyAdmin(admin.ModelAdmin):
    list_display = ('user', 'allergen', 'severity')
    list_filter = ('severity',)
    search_fields = ('user__username', 'allergen')
    autocomplete_fields = ['user']

@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_vegetarian', 'is_vegan', 'is_gluten_free', 'preferred_meal_count', 'budget_preference')
    list_filter = ('is_vegetarian', 'is_vegan', 'is_gluten_free', 'is_dairy_free', 'budget_preference')
    search_fields = ('user__username',)
    autocomplete_fields = ['user']
    
    fieldsets = (
        ('Restricciones Dietéticas', {
            'fields': ('is_vegetarian', 'is_vegan', 'is_gluten_free', 'is_dairy_free', 'is_keto')
        }),
        ('Preferencias Generales', {
            'fields': ('preferred_meal_count', 'max_prep_time', 'budget_preference')
        }),
    )