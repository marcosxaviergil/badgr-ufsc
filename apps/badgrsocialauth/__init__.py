# apps/badgrsocialauth/__init__.py

import logging

# Força o carregamento do provider UFSC ao iniciar o Django
try:
    from allauth.socialaccount.providers import registry
    from .providers.ufsc.provider import UfscProvider

    # Só registra se ainda não estiver registrado
    if not registry.by_id(UfscProvider.id, None):
        registry.register(UfscProvider)
except Exception as e:
    logger = logging.getLogger(__name__)
    logger.warning("[UFSC OAuth2] Falha ao registrar UfscProvider automaticamente: %s", e)
