# authentication/management/commands/create_tokens.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token

User = get_user_model()

class Command(BaseCommand):
    help = 'Crear tokens para usuarios existentes'

    def handle(self, *args, **options):
        users = User.objects.all()
        created_count = 0
        
        for user in users:
            token, created = Token.objects.get_or_create(user=user)
            if created:
                created_count += 1
                self.stdout.write(f'Token creado para {user.username}')
        
        self.stdout.write(
            self.style.SUCCESS(f'Tokens creados: {created_count}')
        )