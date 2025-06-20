# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from django.core.urlresolvers import resolve
from django.contrib.sites.models import Site
from django.contrib.auth import get_user_model
from django.conf import settings
from allauth.socialaccount import providers
from allauth.socialaccount.models import SocialApp
from oauth2_provider.models import Application
from mainsite.models import BadgrApp, ApplicationInfo
from mainsite import views as mainsite_views
import os
import logging
import inspect

logger = logging.getLogger(__name__)


class Command(BaseCommand):
   help = '🔍 Diagnóstico completo e abrangente do fluxo OAuth UFSC'

   def add_arguments(self, parser):
       parser.add_argument(
           '--detailed',
           action='store_true',
           help='🔬 Executar testes mais detalhados e técnicos',
       )
       parser.add_argument(
           '--check-urls',
           action='store_true',
           help='🌐 Testar resolução de URLs específicas',
       )

   def handle(self, *args, **options):
       self.detailed = options.get('detailed', False)
       self.check_urls = options.get('check_urls', False)
       
       self.print_header("🔍 DIAGNÓSTICO COMPLETO DO OAUTH UFSC", "🚀")
       
       # Executar todas as verificações
       self._check_environment_variables()
       self._check_provider_registration()
       self._check_social_app_configuration()
       self._check_settings_configuration()
       self._check_database_secrets()
       self._check_url_routing()
       self._check_middleware_interception()
       self._check_badgr_app_configuration()
       self._check_authentication_backends()
       
       if self.detailed:
           self._detailed_technical_checks()
       
       if self.check_urls:
           self._test_url_resolution()
           
       self._show_summary_and_recommendations()

   def print_header(self, title, emoji="📋"):
       """Imprime cabeçalho formatado"""
       self.stdout.write("\n" + "=" * 80)
       self.stdout.write(f"{emoji} {title}")
       self.stdout.write("=" * 80)

   def print_section(self, title, emoji="🔧"):
       """Imprime seção formatada"""
       self.stdout.write(f"\n{emoji} {title}")
       self.stdout.write("-" * (len(title) + 4))

   def print_check(self, message, status="success", details=None):
       """Imprime resultado de verificação com emoji"""
       if status == "success":
           emoji = "✅"
           style = self.style.SUCCESS
       elif status == "warning":
           emoji = "⚠️"
           style = self.style.WARNING
       elif status == "error":
           emoji = "❌"
           style = self.style.ERROR
       else:
           emoji = "ℹ️"
           style = self.style.HTTP_INFO
           
       self.stdout.write(style(f"  {emoji} {message}"))
       if details:
           for detail in details if isinstance(details, list) else [details]:
               self.stdout.write(f"     • {detail}")

   def _check_environment_variables(self):
       """🌍 Verificar variáveis de ambiente"""
       self.print_section("Verificação de Variáveis de Ambiente", "🌍")
       
       # Verificar variáveis principais
       client_key = os.environ.get('SOCIAL_AUTH_UFSC_OAUTH2_KEY')
       secret_key = os.environ.get('SOCIAL_AUTH_UFSC_OAUTH2_SECRET')
       legacy_secret = os.environ.get('UFSC_OAUTH_SECRET')
       social_providers = os.environ.get('BADGR_SOCIAL_PROVIDERS', '')
       ui_url = os.environ.get('UI_URL')
       
       # Client ID
       if client_key:
           self.print_check(f"SOCIAL_AUTH_UFSC_OAUTH2_KEY: {client_key}", "success")
       else:
           self.print_check("SOCIAL_AUTH_UFSC_OAUTH2_KEY: NÃO DEFINIDA", "error")
           
       # Secret (duas possíveis variáveis)
       if secret_key:
           self.print_check("SOCIAL_AUTH_UFSC_OAUTH2_SECRET: ***", "success")
       elif legacy_secret:
           self.print_check("UFSC_OAUTH_SECRET: *** (variável legada)", "warning", 
                          "Recomendado usar SOCIAL_AUTH_UFSC_OAUTH2_SECRET")
       else:
           self.print_check("Secret OAuth: NÃO DEFINIDA", "error",
                          "Defina SOCIAL_AUTH_UFSC_OAUTH2_SECRET ou UFSC_OAUTH_SECRET")
           
       # Providers habilitados
       if social_providers:
           enabled_providers = [p.strip().lower() for p in social_providers.split(',') if p.strip()]
           if 'ufsc' in enabled_providers:
               self.print_check(f"BADGR_SOCIAL_PROVIDERS: {social_providers}", "success")
           else:
               self.print_check(f"BADGR_SOCIAL_PROVIDERS: {social_providers}", "warning",
                              f"UFSC não está na lista. Providers: {', '.join(enabled_providers)}")
       else:
           self.print_check("BADGR_SOCIAL_PROVIDERS: NÃO DEFINIDA", "error")
           
       # UI URL
       if ui_url:
           self.print_check(f"UI_URL: {ui_url}", "success")
       else:
           self.print_check("UI_URL: usando fallback padrão", "warning")

   def _check_provider_registration(self):
       """🔌 Verificar registro do provider"""
       self.print_section("Verificação do Provider UFSC", "🔌")
       
       try:
           provider = providers.registry.by_id('ufsc')
           self.print_check(f"Provider registrado: {provider.name}", "success")
           self.print_check(f"Classe do provider: {provider.__class__.__name__}", "info")
           
           # Listar todos os providers registrados
           if self.detailed:
               try:
                   provider_map = providers.registry.provider_map
                   provider_list = [f"{pid}: {pcls.name}" for pid, pcls in provider_map.items()]
                   self.print_check("Providers disponíveis:", "info", provider_list)
               except AttributeError:
                   self.print_check("Lista de providers não disponível", "warning")
                   
       except LookupError as e:
           self.print_check(f"Provider UFSC NÃO registrado: {e}", "error",
                          "Verifique se o app 'badgrsocialauth.providers.ufsc' está em INSTALLED_APPS")

   def _check_social_app_configuration(self):
       """📱 Verificar configuração do SocialApp"""
       self.print_section("Verificação do SocialApp", "📱")
       
       try:
           social_app = SocialApp.objects.get(provider='ufsc')
           self.print_check(f"SocialApp encontrado: {social_app.name}", "success")
           self.print_check(f"Client ID: {social_app.client_id}", "info")
           
           # Verificar secret
           if social_app.secret:
               self.print_check(f"Secret configurado: *** ({len(social_app.secret)} caracteres)", "success")
           else:
               self.print_check("Secret NÃO configurado", "error")
               
           # Verificar sites associados
           sites = social_app.sites.all()
           if sites:
               site_domains = [s.domain for s in sites]
               self.print_check(f"Sites associados: {', '.join(site_domains)}", "success")
               
               # Verificar se o site atual está na lista
               current_site = Site.objects.get_current()
               if current_site in sites:
                   self.print_check(f"Site atual ({current_site.domain}) está associado", "success")
               else:
                   self.print_check(f"Site atual ({current_site.domain}) NÃO está associado", "warning")
           else:
               self.print_check("Nenhum site associado", "error",
                              "Associe o SocialApp ao site atual")
               
           # Verificar correspondência com variáveis de ambiente
           expected_client_id = os.environ.get('SOCIAL_AUTH_UFSC_OAUTH2_KEY', 'edx-badges')
           if social_app.client_id == expected_client_id:
               self.print_check("Client ID corresponde à variável de ambiente", "success")
           else:
               self.print_check(f"Client ID difere da variável de ambiente: {expected_client_id}", "warning")
               
       except SocialApp.DoesNotExist:
           self.print_check("SocialApp UFSC NÃO configurado", "error",
                          "Execute: python manage.py setup_initial_data")

   def _check_settings_configuration(self):
       """⚙️ Verificar configurações do Django"""
       self.print_section("Verificação das Configurações", "⚙️")
       
       # SOCIALACCOUNT_PROVIDERS
       if hasattr(settings, 'SOCIALACCOUNT_PROVIDERS'):
           providers_config = getattr(settings, 'SOCIALACCOUNT_PROVIDERS', {})
           if 'ufsc' in providers_config:
               self.print_check("SOCIALACCOUNT_PROVIDERS configurado para UFSC", "success")
               ufsc_config = providers_config.get('ufsc', {})
               
               if 'APP' in ufsc_config:
                   app_config = ufsc_config['APP']
                   self.print_check("Configuração APP presente", "success")
                   if self.detailed:
                       self.print_check(f"Client ID no settings: {app_config.get('client_id', 'N/A')}", "info")
                       self.print_check(f"Secret no settings: {'***' if app_config.get('secret') else 'VAZIO'}", "info")
                       
               if 'SCOPE' in ufsc_config:
                   scopes = ufsc_config['SCOPE']
                   self.print_check(f"Scopes configurados: {', '.join(scopes)}", "info")
                   
           else:
               self.print_check("UFSC não configurado em SOCIALACCOUNT_PROVIDERS", "warning")
       else:
           self.print_check("SOCIALACCOUNT_PROVIDERS não definido", "error")
           
       # Verificar outras configurações importantes
       self.print_check(f"ACCOUNT_AUTHENTICATION_METHOD: {getattr(settings, 'ACCOUNT_AUTHENTICATION_METHOD', 'N/A')}", "info")
       self.print_check(f"ACCOUNT_EMAIL_VERIFICATION: {getattr(settings, 'ACCOUNT_EMAIL_VERIFICATION', 'N/A')}", "info")
       self.print_check(f"SOCIALACCOUNT_AUTO_SIGNUP: {getattr(settings, 'SOCIALACCOUNT_AUTO_SIGNUP', 'N/A')}", "info")

   def _check_database_secrets(self):
       """🔐 Verificar secrets no banco vs configurações"""
       self.print_section("Verificação de Secrets", "🔐")
       
       try:
           social_app = SocialApp.objects.get(provider='ufsc')
           
           # Secret do banco
           db_secret = social_app.secret
           
           # Secret das configurações
           settings_secret = None
           if hasattr(settings, 'SOCIALACCOUNT_PROVIDERS'):
               ufsc_config = settings.SOCIALACCOUNT_PROVIDERS.get('ufsc', {})
               app_config = ufsc_config.get('APP', {})
               settings_secret = app_config.get('secret')
               
           # Comparar
           if db_secret and settings_secret:
               if db_secret == settings_secret:
                   self.print_check("Secret do banco corresponde ao das configurações", "success")
               else:
                   self.print_check("Secret do banco DIFERE das configurações", "warning",
                                  "O banco prevalece sobre as configurações")
           elif db_secret:
               self.print_check("Secret apenas no banco (OK)", "success")
           elif settings_secret:
               self.print_check("Secret apenas nas configurações", "warning",
                               "Execute setup_initial_data para sincronizar")
           else:
               self.print_check("Nenhum secret configurado", "error")
               
       except SocialApp.DoesNotExist:
           self.print_check("SocialApp não existe para verificar secrets", "error")

   def _check_url_routing(self):
       """🌐 Verificar roteamento de URLs"""
       self.print_section("Verificação de Roteamento", "🌐")
       
       urls_to_test = [
           ('/accounts/ufsc/login/', 'Login OAuth UFSC'),
           ('/accounts/ufsc/login/callback/', 'Callback OAuth UFSC'),
           ('/accounts/login/', 'Login geral'),
       ]
       
       for url_path, description in urls_to_test:
           try:
               url_pattern = resolve(url_path)
               view_func = url_pattern.func
               
               # Identificar o tipo de view
               if hasattr(view_func, 'view_class'):
                   view_name = view_func.view_class.__name__
               elif hasattr(view_func, '__name__'):
                   view_name = view_func.__name__
               else:
                   view_name = str(view_func)
                   
               self.print_check(f"{description} → {view_name}", "success")
               
               if self.detailed:
                   self.print_check(f"URL name: {url_pattern.url_name}", "info")
                   
           except Exception as e:
               self.print_check(f"{description} → ERRO: {e}", "error")

   def _check_middleware_interception(self):
       """🛡️ Verificar interceptação por middleware"""
       self.print_section("Verificação de Middleware", "🛡️")
       
       middleware_classes = getattr(settings, 'MIDDLEWARE_CLASSES', [])
       
       # Listar middleware
       if self.detailed:
           self.print_check("Middleware configurados:", "info", middleware_classes)
           
       # Verificar middlewares que podem interceptar
       suspicious_middleware = [
           'mainsite.middleware.MaintenanceMiddleware',
           'badgeuser.middleware.InactiveUserMiddleware'
       ]
       
       for middleware in suspicious_middleware:
           if middleware in middleware_classes:
               self.print_check(f"Middleware presente: {middleware.split('.')[-1]}", "warning",
                              "Pode interceptar requisições de login")
                              
       # Verificar se login_redirect está nas views
       if hasattr(mainsite_views, 'login_redirect'):
           self.print_check("Função login_redirect encontrada", "warning",
                          "Esta função pode estar interceptando logins")
           
           if self.detailed:
               try:
                   source = inspect.getsource(mainsite_views.login_redirect)
                   lines = source.strip().split('\n')
                   self.print_check("Código da função login_redirect:", "info", lines[:10])  # Primeiras 10 linhas
               except:
                   self.print_check("Não foi possível obter o código da função", "warning")

   def _check_badgr_app_configuration(self):
       """🏠 Verificar configuração do BadgrApp"""
       self.print_section("Verificação do BadgrApp", "🏠")
       
       try:
           badgr_app = BadgrApp.objects.get_current()
           self.print_check(f"BadgrApp atual: {badgr_app.cors}", "success")
           
           # Verificar URLs de redirecionamento
           redirects_to_check = [
               ('ui_login_redirect', 'Login UI'),
               ('ui_signup_success_redirect', 'Signup Success'),
               ('email_confirmation_redirect', 'Email Confirmation'),
               ('oauth_authorization_redirect', 'OAuth Authorization'),
           ]
           
           for field, description in redirects_to_check:
               url = getattr(badgr_app, field, None)
               if url:
                   self.print_check(f"{description}: {url}", "info")
               else:
                   self.print_check(f"{description}: NÃO CONFIGURADO", "warning")
                   
           # Verificar se é padrão
           if badgr_app.is_default:
               self.print_check("Configurado como BadgrApp padrão", "success")
           else:
               self.print_check("NÃO é o BadgrApp padrão", "warning")
               
       except Exception as e:
           self.print_check(f"Erro ao verificar BadgrApp: {e}", "error")

   def _check_authentication_backends(self):
       """🔒 Verificar backends de autenticação"""
       self.print_section("Verificação de Backends", "🔒")
       
       backends = getattr(settings, 'AUTHENTICATION_BACKENDS', [])
       
       # Backends importantes para OAuth
       important_backends = [
           'allauth.account.auth_backends.AuthenticationBackend',
           'django.contrib.auth.backends.ModelBackend',
       ]
       
       for backend in important_backends:
           if backend in backends:
               self.print_check(f"Backend presente: {backend.split('.')[-1]}", "success")
           else:
               self.print_check(f"Backend ausente: {backend.split('.')[-1]}", "warning")
               
       if self.detailed:
           self.print_check("Todos os backends:", "info", 
                          [b.split('.')[-1] for b in backends])

   def _detailed_technical_checks(self):
       """🔬 Verificações técnicas detalhadas"""
       self.print_section("Verificações Técnicas Detalhadas", "🔬")
       
       # Verificar versões
       import django
       import allauth
       
       self.print_check(f"Django: {django.get_version()}", "info")
       self.print_check(f"django-allauth: {allauth.__version__}", "info")
       
       # Verificar usuários no sistema
       User = get_user_model()
       user_count = User.objects.count()
       self.print_check(f"Usuários no sistema: {user_count}", "info")
       
       # Verificar Applications OAuth2
       app_count = Application.objects.count()
       self.print_check(f"OAuth2 Applications: {app_count}", "info")
       
       if app_count > 0:
           try:
               public_app = Application.objects.get(client_id='public')
               self.print_check(f"Application 'public' presente: {public_app.name}", "success")
           except Application.DoesNotExist:
               self.print_check("Application 'public' não encontrada", "warning")

   def _test_url_resolution(self):
       """🧪 Testar resolução de URLs específicas"""
       self.print_section("Teste de Resolução de URLs", "🧪")
       
       test_urls = [
           '/accounts/',
           '/accounts/ufsc/',
           '/accounts/ufsc/login/',
           '/accounts/ufsc/login/callback/',
           '/auth/login/',
           '/o/token/',
           '/o/authorize/',
       ]
       
       for url in test_urls:
           try:
               pattern = resolve(url)
               self.print_check(f"{url} → ✓", "success")
           except Exception as e:
               self.print_check(f"{url} → ❌ {e}", "error")

   def _show_summary_and_recommendations(self):
       """📋 Resumo e recomendações"""
       self.print_section("Resumo e Recomendações", "📋")
       
       # URLs importantes
       ui_url = os.environ.get('UI_URL', 'https://badges.setic.ufsc.br')
       
       self.print_check("URLs para configurar no servidor OAuth UFSC:", "info", [
           f"Login: {ui_url}/accounts/ufsc/login/",
           f"Callback: {ui_url}/accounts/ufsc/login/callback/",
       ])
       
       self.print_check("Para testar o OAuth:", "info", [
           f"1. Acesse: {ui_url}/accounts/ufsc/login/",
           "2. Deve redirecionar para sistemas.ufsc.br",
           "3. Após login, deve retornar para o sistema",
       ])
       
       self.print_check("Comandos úteis:", "info", [
           "python manage.py test_oauth_flow --detailed",
           "python manage.py setup_initial_data",
           "python manage.py test_local_login",
       ])
       
       self.print_header("Diagnóstico Concluído", "🎉")
