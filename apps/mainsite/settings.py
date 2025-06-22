# apps/mainsite/settings.py

import sys
import os

from mainsite import TOP_DIR
import logging

INSTALLED_APPS = [
    'mainsite',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
    'django_object_actions',
    'markdownify',
    'badgeuser',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'badgrsocialauth',
    'badgrsocialauth.providers.ufsc',  # ✅ MANTER para disponibilizar no dropdown
    'allauth.socialaccount.providers.azure',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.linkedin_oauth2',
    'allauth.socialaccount.providers.oauth2',
    'corsheaders',
    'rest_framework',
    'rest_framework.authtoken',
    'django_celery_results',
    'oauth2_provider',
    'entity',
    'issuer',
    'backpack',
    'pathway',
    'recipient',
    'externaltools',
    'apispec_drf',
    'composition',
]

# Compativel com Django 1.11 e corsheaders==1.1.0
MIDDLEWARE_CLASSES = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'oauth2_provider.middleware.OAuth2TokenMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'mainsite.middleware.MaintenanceMiddleware',
    'badgeuser.middleware.InactiveUserMiddleware',
    'mainsite.middleware.UFSCOnlyAuthMiddleware',
]

ROOT_URLCONF = 'mainsite.urls'
ALLOWED_HOSTS = ['api-badges.setic.ufsc.br', 'badges.setic.ufsc.br', 'localhost']
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'OPTIONS': {
            'context_processors': [
                'django.contrib.auth.context_processors.auth',
                'django.template.context_processors.debug',
                'django.template.context_processors.i18n',
                'django.template.context_processors.media',
                'django.template.context_processors.static',
                'django.template.context_processors.tz',
                'django.contrib.messages.context_processors.messages',
                'mainsite.context_processors.extra_settings'
            ],
            'loaders': (
                'django.template.loaders.app_directories.Loader',
                'django.template.loaders.filesystem.Loader',
            ),
        },
    },
]

HTTP_ORIGIN = "https://api-badges.setic.ufsc.br"

STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

STATIC_ROOT = os.path.join(TOP_DIR, 'staticfiles')
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    os.path.join(TOP_DIR, 'apps', 'mainsite', 'static'),
]

AUTH_USER_MODEL = 'badgeuser.BadgeUser'
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/docs'

AUTHENTICATION_BACKENDS = [
    'oauth2_provider.backends.OAuth2Backend',
    'rules.permissions.ObjectPermissionBackend',
    "badgeuser.backends.CachedModelBackend",
    "badgeuser.backends.CachedAuthenticationBackend",
    'allauth.account.auth_backends.AuthenticationBackend',
]

ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
ACCOUNT_ADAPTER = 'mainsite.account_adapter.BadgrAccountAdapter'
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_EMAIL_REQUIRED = True
ACCOUNT_USERNAME_REQUIRED = False
ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_LOGOUT_ON_GET = True
ACCOUNT_AUTHENTICATION_METHOD = 'email'
ACCOUNT_FORMS = {
    'add_email': 'badgeuser.account_forms.AddEmailForm'
}
ACCOUNT_SIGNUP_FORM_CLASS = 'badgeuser.forms.BadgeUserCreationForm'

SOCIALACCOUNT_EMAIL_REQUIRED = False
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'

# ✅ CORREÇÃO: REMOVER configuração automática do UFSC
# Agora será configurado manualmente via admin
SOCIALACCOUNT_PROVIDERS = {
    'azure': {
        'VERIFIED_EMAIL': True
    },
    'linkedin_oauth2': {
        'VERIFIED_EMAIL': True
    }
    # ✅ UFSC removido - será configurado via admin interface
}

SOCIALACCOUNT_ADAPTER = 'badgrsocialauth.adapter.BadgrSocialAccountAdapter'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', 'OPTIONS': {'min_length': 8}},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ✅ CONFIGURAÇÕES PARA OAUTH UFSC EXCLUSIVO
OPEN_FOR_SIGNUP = False  # ✅ Desabilitar cadastro local via API

CORS_ORIGIN_ALLOW_ALL = True
#CORS_ALLOWED_ORIGINS = [
#    'https://badges.setic.ufsc.br',
#    'https://api-badges.setic.ufsc.br',
#    'http://localhost:4200',
#    'http://localhost:8080',
#]
CORS_URLS_REGEX = r'^.*$'
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]
CORS_EXPOSE_HEADERS = ['link']

MEDIA_ROOT = os.path.join(TOP_DIR, 'mediafiles')
MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = STATIC_URL+'admin/'

FIXTURE_DIRS = [os.path.join(TOP_DIR, 'etc', 'fixtures')]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': [],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'stream': sys.stdout,
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins', 'console'],
            'level': 'ERROR',
            'propagate': True,
        },
        'Badgr.Events': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'corsheaders': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        }
    },
    'formatters': {
        'default': {'format': '%(asctime)s %(levelname)s %(module)s %(message)s'},
        'json': {
            '()': 'mainsite.formatters.JsonFormatter',
            'format': '%(asctime)s',
            'datefmt': '%Y-%m-%dT%H:%M:%S%z',
        }
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'KEY_PREFIX': 'badgr_',
        'VERSION': 10,
        'TIMEOUT': None,
    }
}

MAINTENANCE_MODE = False
MAINTENANCE_URL = '/maintenance'

SPHINX_API_VERSION = 0x116
TEST_RUNNER = 'mainsite.testrunner.BadgrRunner'

REST_FRAMEWORK = {
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.DjangoModelPermissionsOrAnonReadOnly'],
    'DEFAULT_RENDERER_CLASSES': (
        'mainsite.renderers.JSONLDRenderer',
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ),
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'mainsite.authentication.BadgrOAuth2Authentication',
        'rest_framework.authentication.TokenAuthentication',
        'entity.authentication.ExplicitCSRFSessionAuthentication',
    ),
    'DEFAULT_VERSIONING_CLASS': 'rest_framework.versioning.URLPathVersioning',
    'DEFAULT_VERSION': 'v1',
    'ALLOWED_VERSIONS': ['v1','v2'],
    'EXCEPTION_HANDLER': 'entity.views.exception_handler',
    'PAGE_SIZE': 100,
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
}

REMOTE_DOCUMENT_FETCHER = 'badgeanalysis.utils.get_document_direct'
LINKED_DATA_DOCUMENT_FETCHER = 'badgeanalysis.utils.custom_docloader'

LTI_STORE_IN_SESSION = False
CAIROSVG_VERSION_SUFFIX = "2"
SITE_ID = 1
USE_I18N = False
USE_L10N = False
USE_TZ = True

MARKDOWNIFY_WHITELIST_TAGS = [
    'h1','h2','h3','h4','h5','h6','a','abbr','acronym','b','blockquote','em','i',
    'li','ol','p','strong','ul','code','pre','hr'
]

OAUTH2_PROVIDER = {
    'SCOPES': {
        'r:profile':   'See who you are',
        'rw:profile':  'Update your own user profile',
        'r:backpack':  'List assertions in your backpack',
        'rw:backpack': 'Upload badges into a backpack',
        'rw:issuer':   'Create and update issuers, create and update badge classes, and award assertions',
        'rw:issuer:*':  'Create and update badge classes, and award assertions for a single issuer',
        'rw:serverAdmin': 'Superuser trusted operations on most objects',
        'r:assertions': 'Batch receive assertions',
    },
    'DEFAULT_SCOPES': ['r:profile'],
    'OAUTH2_VALIDATOR_CLASS': 'mainsite.oauth_validator.BadgrRequestValidator',
    'ACCESS_TOKEN_EXPIRE_SECONDS': 86400
}
OAUTH2_PROVIDER_APPLICATION_MODEL = 'oauth2_provider.Application'
OAUTH2_PROVIDER_ACCESS_TOKEN_MODEL = 'oauth2_provider.AccessToken'
OAUTH2_TOKEN_SESSION_TIMEOUT_SECONDS = OAUTH2_PROVIDER['ACCESS_TOKEN_EXPIRE_SECONDS']

API_DOCS_EXCLUDED_SCOPES = ['rw:issuer:*', 'r:assertions', 'rw:serverAdmin', '*']

BADGR_PUBLIC_BOT_USERAGENTS = ['LinkedInBot', 'Twitterbot', 'facebook', 'Facebot', 'Slackbot', 'Embedly']
BADGR_PUBLIC_BOT_USERAGENTS_WIDE = ['LinkedInBot', 'Twitterbot', 'facebook', 'Facebot']

CELERY_ALWAYS_EAGER = True
BADGERANK_NOTIFY_ON_BADGECLASS_CREATE = True
BADGERANK_NOTIFY_ON_FIRST_ASSERTION = True
BADGERANK_NOTIFY_URL = 'https://api.badgerank.org/v1/badgeclass/submit'
BADGR_APPROVED_ISSUERS_ONLY = False

# ========== DESABILITAR SISTEMA DE TERMS OF SERVICE COMPLETAMENTE ==========
# Forca desabilitacao total do sistema de termos identificado na investigacao

# Desabilitar GDPR compliance que forca termos
GDPR_COMPLIANCE_NOTIFY_ON_FIRST_AWARD = False

# Garantir que URLs de termos sejam None
PRIVACY_POLICY_URL = None
TERMS_OF_SERVICE_URL = None
GDPR_INFO_URL = None
OPERATOR_STREET_ADDRESS = None
OPERATOR_NAME = None
OPERATOR_URL = None

# Desabilitar verificacao de termos no backend
BADGR_TERMS_VERSION = None
BADGR_PRIVACY_VERSION = None

# Configuracoes do AllAuth para nao forcar termos
ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL = None
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = None

# Configuracao para frontend nao exibir popup de termos
UI_DISABLE_TERMS_POPUP = True
SHOW_TERMS_POPUP = False
REQUIRE_TERMS_ACCEPTANCE = False

# Desabilitar middleware que pode forcar termos (se existir)
MIDDLEWARE_CLASSES = [m for m in MIDDLEWARE_CLASSES if 'terms' not in m.lower()]

# ===== AUTHCODE_SECRET_KEY CORRECTION =====
# Corrigir problema de chave invalida que estava causando erro 500
from cryptography.fernet import Fernet

# Tentar pegar da variavel de ambiente primeiro
AUTHCODE_SECRET_KEY = os.environ.get('AUTHCODE_SECRET_KEY')

if not AUTHCODE_SECRET_KEY:
    # Se nao esta definida na env, usar uma chave fixa valida para desenvolvimento
    # EM PRODUCAO: sempre definir AUTHCODE_SECRET_KEY no docker-compose.yml
    AUTHCODE_SECRET_KEY = 'ZmDfcTF7_60GrrY167zsiPd67pEvs0aGOv2oasOM92s='
    print("WARNING: Usando AUTHCODE_SECRET_KEY padrao - defina no docker-compose.yml para producao")

# Converter para bytes se necessario
if isinstance(AUTHCODE_SECRET_KEY, str):
    AUTHCODE_SECRET_KEY = AUTHCODE_SECRET_KEY.encode('utf-8')

# Verificar se a chave e valida
try:
    Fernet(AUTHCODE_SECRET_KEY)
    print("[OK] AUTHCODE_SECRET_KEY valida")
except Exception as e:
    print("[ERRO] AUTHCODE_SECRET_KEY invalida: {}".format(e))
    # Gerar uma nova como fallback
    AUTHCODE_SECRET_KEY = Fernet.generate_key()
    print("[INFO] Gerando nova chave: {}".format(AUTHCODE_SECRET_KEY.decode()))

AUTHCODE_EXPIRES_SECONDS = 600

SAML_EMAIL_KEYS = ['Email', 'mail']
SAML_FIRST_NAME_KEYS = ['FirstName', 'givenName']
SAML_LAST_NAME_KEYS = ['LastName', 'sn']