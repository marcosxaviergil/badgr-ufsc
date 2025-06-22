from django.conf import settings
from django.http import HttpResponseRedirect, HttpResponsePermanentRedirect
from mainsite.models import BadgrApp


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


# ✅ ADICIONADO: Middleware para OAuth UFSC exclusivo
class UFSCOnlyAuthMiddleware(object):
    """
    Middleware para redirecionar tentativas de auth local para OAuth UFSC
    """
    def __init__(self, get_response=None):
        self.get_response = get_response

    def __call__(self, request):
        return self.process_request(request) or self.get_response(request)

    def process_request(self, request):
        # URLs que devem ser redirecionadas para OAuth
        auth_paths = [
            '/v1/user/profile',  # Cadastro via API
            '/v2/users',         # Cadastro via API v2
            '/auth/password',    # Mudança de senha
        ]
        
        # Se for POST para endpoints de auth local, redirecionar
        if request.method == 'POST' and any(path in request.path for path in auth_paths):
            try:
                badgr_app = BadgrApp.objects.get_current(request)
                return HttpResponseRedirect(f'https://{badgr_app.cors}/auth/login/')
            except:
                return HttpResponseRedirect('https://badges.setic.ufsc.br/auth/login/')
        
        return None
