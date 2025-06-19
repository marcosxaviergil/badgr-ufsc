from django.core.exceptions import ImproperlyConfigured
from django.urls import reverse, NoReverseMatch
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.utils.deprecation import MiddlewareMixin


class InactiveUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if not hasattr(request, 'user'):
            raise ImproperlyConfigured(
                "The Django remote user auth middleware requires the"
                " authentication middleware to be installed.  Edit your"
                " MIDDLEWARE setting to insert"
                " 'django.contrib.auth.middleware.AuthenticationMiddleware'"
                " before the InactiveUserMiddleware class.")
        
        # Em Django 1.11, is_authenticated é uma propriedade, não um método
        if request.user.is_authenticated and not request.user.is_active:
            try:
                account_enabled_url = reverse('account_enabled')
                if request.path != account_enabled_url:
                    return HttpResponseRedirect(account_enabled_url)
            except NoReverseMatch:
                # Se a URL não existir, retorna forbidden
                return HttpResponseForbidden('Sua conta está inativa. Entre em contato com o administrador.')
