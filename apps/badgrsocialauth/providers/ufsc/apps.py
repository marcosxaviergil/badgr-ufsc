# apps/badgrsocialauth/providers/ufsc/apps.py
# CORREÇÃO PERMANENTE

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class UfscProviderConfig(AppConfig):
    name = 'badgrsocialauth.providers.ufsc'
    label = 'badgrsocialauth_providers_ufsc'
    verbose_name = _('Badgr Social Auth UFSC Provider')
    
    def ready(self):
        """Registrar provider quando Django estiver completamente carregado"""
        import sys
        
        # Pular registro durante comandos específicos
        skip_commands = ['migrate', 'makemigrations', 'check', 'collectstatic']
        if any(cmd in sys.argv for cmd in skip_commands):
            return
            
        try:
            from .provider import UfscProvider
            from allauth.socialaccount import providers
            
            # CORREÇÃO: Método compatível com Django 1.11
            try:
                existing = providers.registry.by_id('ufsc')
                # Já registrado
            except:
                # Não registrado, vamos registrar
                providers.registry.register(UfscProvider)
                
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning(f"[UFSC OAuth] Erro no registro: {e}")