# apps/badgrsocialauth/providers/ufsc/apps.py

from django.apps import AppConfig


class UfscProviderConfig(AppConfig):
    name = 'badgrsocialauth.providers.ufsc'
    label = 'badgrsocialauth_providers_ufsc' 
    verbose_name = 'UFSC OAuth Provider'
    
    def ready(self):
        """
        O provider é registrado no provider.py
        Não fazemos nada aqui
        """
        pass