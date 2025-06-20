# apps/badgrsocialauth/__init__.py

# Força o carregamento do provider UFSC ao iniciar o Django
try:
    from allauth.socialaccount.providers import registry
    from .providers.ufsc.provider import UfscProvider
    if not registry.by_id(UfscProvider.id, None):
        registry.register(UfscProvider)
except Exception as e:
    import logging
    logging.getLogger(__name__).warning(f"[UFSC OAuth2] Falha ao registrar UfscProvider automaticamente: {e}")
