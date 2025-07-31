# recommendations/management/commands/initialize_profiles.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from recommendations.models import NutritionalProfile

User = get_user_model()

class Command(BaseCommand):
    help = 'Inicializar perfiles nutricionales para usuarios existentes'

    def handle(self, *args, **options):
        users = User.objects.filter(profile_completed=True)
        created_count = 0
        
        for user in users:
            profile, created = NutritionalProfile.objects.get_or_create(
                user=user,
                defaults={
                    'target_calories': user.daily_calories or user.calculate_daily_calories() or 2000,
                    'target_protein': user.daily_protein or 150,
                    'target_carbs': user.daily_carbs or 250,
                    'target_fat': user.daily_fat or 65,
                    'target_fiber': 25,
                    'max_sodium': 2300,
                    'min_calcium': 1000,
                    'min_iron': 8,
                    'min_vitamin_c': 90
                }
            )
            
            if created:
                created_count += 1
                self.stdout.write(f'Perfil creado para {user.username}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Perfiles nutricionales inicializados: {created_count}')
        )