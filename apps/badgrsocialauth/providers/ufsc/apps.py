# apps/badgrsocialauth/providers/ufsc/apps.py

from django.apps import AppConfig


class UfscProviderConfig(AppConfig):
    name = 'badgrsocialauth.providers.ufsc'
    label = 'badgrsocialauth_providers_ufsc'
    verbose_name = 'Badgr Social Auth UFSC Provider'
    
    def ready(self):
        """Registrar provider quando Django estiver completamente carregado"""
        import sys
        
        # Só registrar se não estamos em commands
        if any(cmd in sys.argv for cmd in ['migrate', 'makemigrations', 'check', 'collectstatic']):
            return
            
        try:
            from allauth.socialaccount import providers
            from .provider import UfscProvider
            
            # Forçar registro mesmo se já existir
            providers.registry.register(UfscProvider)
            
        except Exception:
            pass