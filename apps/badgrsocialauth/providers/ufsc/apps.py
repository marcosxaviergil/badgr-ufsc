# apps/badgrsocialauth/providers/ufsc/apps.py

from django.apps import AppConfig


class UfscProviderConfig(AppConfig):
    name = 'badgrsocialauth.providers.ufsc'
    label = 'badgrsocialauth_providers_ufsc'
    verbose_name = 'Badgr Social Auth UFSC Provider'
    
    def ready(self):
        """Registrar provider quando Django estiver completamente carregado"""
        import sys
        
        # Pular registro durante comandos específicos
        skip_commands = ['migrate', 'makemigrations', 'check', 'collectstatic']
        if any(cmd in sys.argv for cmd in skip_commands):
            return
            
        try:
            from allauth.socialaccount import providers
            from .provider import UfscProvider
            
            # Verificar se já está registrado
            try:
                existing = providers.registry.by_id('ufsc')
                print("[UFSC] Provider já registrado: {}".format(existing.name))
            except:
                # Não registrado, vamos registrar
                providers.registry.register(UfscProvider)
                print("[UFSC] Provider registrado com sucesso: {}".format(UfscProvider.name))
                
        except Exception as e:
            import logging
            logging.getLogger(__name__).warning("[UFSC OAuth] Erro no registro: {}".format(e))