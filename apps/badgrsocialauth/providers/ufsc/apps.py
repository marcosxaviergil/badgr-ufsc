# apps/badgrsocialauth/providers/ufsc/apps.py

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class UfscProviderConfig(AppConfig):
    name = 'badgrsocialauth.providers.ufsc'
    label = 'badgrsocialauth_providers_ufsc'
    verbose_name = _('Badgr Social Auth UFSC Provider')
    
    def ready(self):
        """Registrar provider quando Django estiver completamente carregado"""
        try:
            # Só registrar se apps estão carregados e não estamos em migração
            from django.apps import apps
            from django.core.management import get_commands
            
            # Verificar se não estamos executando comandos de migração
            import sys
            if any(cmd in sys.argv for cmd in ['migrate', 'makemigrations', 'check']):
                return
                
            if apps.ready:
                from .provider import UfscProvider
                from allauth.socialaccount import providers
                
                # Verificar se não está já registrado para evitar duplicação
                if not providers.registry.by_id('ufsc', raise_exception=False):
                    providers.registry.register(UfscProvider)
                    
        except Exception as e:
            # Não imprimir erro durante startup para evitar spam nos logs
            pass
