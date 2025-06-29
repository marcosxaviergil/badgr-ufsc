# apps/badgrsocialauth/providers/ufsc/apps.py

from django.apps import AppConfig


class UfscProviderConfig(AppConfig):
    name = 'badgrsocialauth.providers.ufsc'
    label = 'badgrsocialauth_providers_ufsc' 
    verbose_name = 'UFSC OAuth Provider'
    
    def ready(self):
        """
        ✅ CORREÇÃO: Import tardio para evitar problemas de registro
        """
        try:
            # Import para registrar o provider depois que Django está pronto
            from . import provider
        except ImportError:
            pass  # Ignorar se houver problema de import
