# apps/mainsite/middleware.py

from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect


class MaintenanceMiddleware(object):
    """Redireciona para a página de manutenção se ativado."""
    def process_request(self, request):
        if getattr(settings, 'MAINTENANCE_MODE', False) and hasattr(settings, 'MAINTENANCE_URL'):
            return HttpResponseRedirect(settings.MAINTENANCE_URL)
        return None


class TrailingSlashMiddleware(object):
    """Adiciona ou remove barra no final da URL, conforme o padrão definido."""
    def process_request(self, request):
        exceptions = ['/staff', '/__debug__']
        if any(request.path.startswith(e) for e in exceptions):
            if not request.path.endswith('/'):
                return HttpResponsePermanentRedirect(request.path + '/')
        else:
            if request.path != '/' and request.path.endswith('/'):
                return HttpResponsePermanentRedirect(request.path[:-1])
        return None
