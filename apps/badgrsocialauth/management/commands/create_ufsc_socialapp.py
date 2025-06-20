# apps/badgrsocialauth/management/commands/create_ufsc_socialapp.py

from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
import os


class Command(BaseCommand):
    help = 'Cria SocialApp para OAuth UFSC'

    def handle(self, *args, **options):
        site = Site.objects.get_current()
        
        app, created = SocialApp.objects.get_or_create(
            provider='ufsc',
            defaults={
                'name': 'UFSC OAuth',
                'client_id': os.environ.get('UFSC_OAUTH2_CLIENT_ID', 'edx-badges'),
                'secret': os.environ.get('UFSC_OAUTH2_CLIENT_SECRET', 'sdf46sdfgsddfg'),
            }
        )
        
        app.sites.add(site)
        
        if created:
            self.stdout.write(self.style.SUCCESS('SocialApp UFSC criado com sucesso'))
        else:
            self.stdout.write(self.style.WARNING('SocialApp UFSC já existe'))
            # Atualizar credenciais se mudaram
            app.client_id = os.environ.get('UFSC_OAUTH2_CLIENT_ID', 'edx-badges')
            app.secret = os.environ.get('UFSC_OAUTH2_CLIENT_SECRET', 'sdf46sdfgsddfg')
            app.save()
            self.stdout.write(self.style.SUCCESS('Credenciais atualizadas'))
