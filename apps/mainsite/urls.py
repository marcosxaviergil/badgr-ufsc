# apps/mainsite/urls.py

from django.apps import apps
from django.conf import settings
from django.conf.urls import url, include
from django.contrib import admin
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from mainsite.admin import badgr_admin
from mainsite.oauth2_api import AuthorizationApiView, TokenView, AuthCodeExchange

badgr_admin.autodiscover()

from django.views.generic.base import RedirectView, TemplateView
from oauth2_provider.urls import base_urlpatterns as oauth2_provider_base_urlpatterns

from mainsite.views import SitewideActionFormView, LoginAndObtainAuthToken, RedirectToUiLogin, DocsAuthorizeRedirect
from mainsite.views import info_view, email_unsubscribe, AppleAppSiteAssociation, error404, error500, token_login
from pathway.api import PathwayList
from allauth.account.views import LoginView


# ✅ Health check inline
def health_check(request):
    return JsonResponse({'status': 'ok', 'timestamp': '2025-06-18'})


# ✅ Redirecionamento de login para OAuth2 - CORRIGIDO
def login_redirect(request):
    """Redireciona para login OAuth UFSC ou retorna info de autenticação"""
    if request.method == 'GET':
        return JsonResponse({
            'loginUrl': '/accounts/ufsc/login/',
            'tokenUrl': '/api/v2/auth/token-login/',
            'method': 'POST',
            'message': 'Use OAuth UFSC or token-based authentication'
        })
    elif request.method == 'POST':
        return token_login(request)
    else:
        return JsonResponse({'error': 'Method not allowed'}, status=405)


urlpatterns = [
    # ✅ ENDPOINTS PRINCIPAIS - ORDEM IMPORTANTE
    url(r'^$', info_view, name='index'),  # ✅ CORRIGIDO: info_view retorna JSON
    url(r'^api/health/?$', health_check, name='health_check'),
    
    # ✅ AUTHENTICATION ENDPOINTS
    url(r'^api/v2/auth/token-login/?$', token_login, name='token_login'),
    url(r'^api-auth/token/?$', login_redirect, name='api_auth_token_override'),
    url(r'^api/auth/token/?$', login_redirect, name='api_auth_token_alt'),
    
    # ✅ OAUTH2 ENDPOINTS - ORDEM CORRETA
    url(r'^o/authorize/?$', AuthorizationApiView.as_view(), name='oauth2_api_authorize'),
    url(r'^o/token/?$', TokenView.as_view(), name='oauth2_provider_token'),
    url(r'^o/code/?$', AuthCodeExchange.as_view(), name='oauth2_code_exchange'),
    url(r'^o/', include(oauth2_provider_base_urlpatterns, namespace='oauth2_provider')),

    # ✅ STATIC FILES
    url(r'^favicon\.png/?$', RedirectView.as_view(url='%simages/favicon.png' % settings.STATIC_URL, permanent=True)),
    url(r'^favicon\.ico/?$', RedirectView.as_view(url='%simages/favicon.png' % settings.STATIC_URL, permanent=True)),
    url(r'^robots\.txt$', RedirectView.as_view(url='%srobots.txt' % settings.STATIC_URL, permanent=True)),
    url(r'^apple-app-site-association', AppleAppSiteAssociation.as_view(), name="apple-app-site-association"),

    # ✅ UFSC OAUTH - INCLUIR ANTES DE ACCOUNTS GENÉRICO
    url(r'^accounts/ufsc/', include('badgrsocialauth.providers.ufsc.urls')),
    
    # ✅ AUTHENTICATION - INTERCEPTAR LOGIN
    url(r'^accounts/login/?$', login_redirect, name='account_login'),
    url(r'^accounts/', include('badgrsocialauth.urls')),
    url(r'^accounts/', include('allauth.urls')),

    # ✅ ADMIN INTERFACES
    url(r'^admin/', admin.site.urls),
    url(r'^staff/sidewide-actions$', SitewideActionFormView.as_view(), name='badgr_admin_sitewide_actions'),
    url(r'^staff/', include(badgr_admin.urls)),

    # ✅ DOCUMENTATION
    url(r'^docs/oauth2/authorize$', DocsAuthorizeRedirect.as_view(), name='docs_authorize_redirect'),
    url(r'^docs/?$', RedirectView.as_view(url='/docs/v2/', permanent=True)),
    url(r'^docs/', include('apispec_drf.urls')),

    # ✅ UTILITIES
    url(r'^json-ld/', include('badgrlog.urls')),
    url(r'^unsubscribe/(?P<email_encoded>[^/]+)/(?P<expiration>[^/]+)/(?P<signature>[^/]+)', email_unsubscribe, name='unsubscribe'),

    # ✅ PUBLIC APIS
    url(r'^public/', include('issuer.public_api_urls'), kwargs={'version': 'v2'}),
    url(r'^public/', include('pathway.public_api_urls'), kwargs={'version': 'v2'}),
    url(r'', include('backpack.share_urls')),

    # ✅ API V1 ENDPOINTS
    url(r'^v1/user/', include('badgeuser.v1_api_urls'), kwargs={'version': 'v1'}),
    url(r'^v1/user/', include('badgrsocialauth.v1_api_urls'), kwargs={'version': 'v1'}),
    url(r'^v1/issuer/', include('issuer.v1_api_urls'), kwargs={'version': 'v1'}),
    url(r'^v1/earner/', include('backpack.v1_api_urls'), kwargs={'version': 'v1'}),

    # ✅ API V2 ENDPOINTS  
    url(r'^v2/issuers/(?P<issuer_slug>[^/]+)/pathways$', PathwayList.as_view(), name='pathway_list'),
    url(r'^v2/issuers/(?P<issuer_slug>[^/]+)/pathways/', include('pathway.api_urls'), kwargs={'version': 'v1'}),
    url(r'^v2/', include('recipient.v1_api_urls'), kwargs={'version': 'v1'}),
    url(r'^v2/', include('issuer.v2_api_urls'), kwargs={'version': 'v2'}),
    url(r'^v2/', include('badgeuser.v2_api_urls'), kwargs={'version': 'v2'}),
    url(r'^v2/', include('badgrsocialauth.v2_api_urls'), kwargs={'version': 'v2'}),
    url(r'^v2/backpack/', include('backpack.v2_api_urls'), kwargs={'version': 'v2'}),

    # ✅ EXTERNAL TOOLS
    url(r'^v1/externaltools/', include('externaltools.v1_api_urls'), kwargs={'version': 'v1'}),
    url(r'^v2/externaltools/', include('externaltools.v2_api_urls'), kwargs={'version': 'v2'}),
    url(r'^externaltools/', include('externaltools.v1_api_urls'), kwargs={'version': 'v1'}),
]

# ✅ DEBUG CONFIGURATIONS
if getattr(settings, 'DEBUG_ERRORS', False):
    urlpatterns = [
        url(r'^error/404/?$', error404, name='404'),
        url(r'^error/500/?$', error500, name='500'),
    ] + urlpatterns

if getattr(settings, 'DEBUG_MEDIA', True):
    from django.views.static import serve as static_serve
    media_url = getattr(settings, 'MEDIA_URL', '/media/').lstrip('/')
    urlpatterns = [
        url(r'^media/(?P<path>.*)$', static_serve, {'document_root': settings.MEDIA_ROOT}),
    ] + urlpatterns

if getattr(settings, 'DEBUG_STATIC', True):
    from django.contrib.staticfiles.views import serve as staticfiles_serve
    static_url = getattr(settings, 'STATIC_URL', '/static/').replace(getattr(settings, 'HTTP_ORIGIN', ''), '').lstrip('/')
    urlpatterns = [
        url(r'^%s(?P<path>.*)' % (static_url,), staticfiles_serve, kwargs={'insecure': True}),
    ] + urlpatterns

if getattr(settings, 'DEBUG', True) or getattr(settings, 'SERVE_PATTERN_LIBRARY', False):
    urlpatterns = [
        url(r'^component-library$', TemplateView.as_view(template_name='component-library.html'), name='component-library')
    ] + urlpatterns

if settings.DEBUG and apps.is_installed('debug_toolbar'):
    try:
        import debug_toolbar
        urlpatterns = urlpatterns + [url(r'^__debug__/', include(debug_toolbar.urls))]
    except ImportError:
        pass

handler404 = error404
handler500 = error500
