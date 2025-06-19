# apps/badgeuser/management/commands/test_email_confirmation_system.py

import re
import urllib.parse
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.urls import reverse
from django.utils import timezone
from allauth.account.models import EmailConfirmationHMAC
from allauth.account.utils import user_pk_to_url_str
from allauth.account.adapter import get_adapter
from badgeuser.models import CachedEmailAddress
from mainsite.models import BadgrApp, AccessTokenProxy
from badgeuser.api import BadgeUserEmailConfirm
from oauth2_provider.models import Application


class Command(BaseCommand):
    help = 'Testa o sistema completo de confirmação de email após correções'

    def add_arguments(self, parser):
        parser.add_argument(
            '--test-email',
            type=str,
            default='teste@ufsc.br',
            help='Email para usar nos testes'
        )
        parser.add_argument(
            '--create-test-user',
            action='store_true',
            help='Criar usuário de teste se não existir'
        )

    def handle(self, *args, **options):
        self.test_email = options['test_email']
        self.create_test_user = options['create_test_user']
        
        self.stdout.write(self.style.SUCCESS('\n=== TESTE COMPLETO DO SISTEMA DE CONFIRMAÇÃO DE EMAIL ===\n'))
        
        # Executar todos os testes
        self.test_django_settings()
        self.test_badgr_app_configuration()
        self.test_oauth_configuration()
        self.test_allauth_configuration()
        self.test_url_generation()
        self.test_email_confirmation_view()
        
        if self.create_test_user:
            self.test_complete_flow()
        
        self.stdout.write(self.style.SUCCESS('\n=== RESUMO DOS TESTES ==='))
        self.show_final_summary()

    def test_django_settings(self):
        """Testa as configurações básicas do Django"""
        self.stdout.write(self.style.WARNING('\n1. TESTANDO CONFIGURAÇÕES DO DJANGO'))
        
        errors = []
        warnings = []
        
        # Verificar configurações críticas
        ui_url = getattr(settings, 'UI_URL', None)
        http_origin = getattr(settings, 'HTTP_ORIGIN', None)
        
        if not ui_url:
            errors.append("UI_URL não configurado")
        elif 'https://https://' in ui_url:
            errors.append(f"UI_URL com duplo https://: {ui_url}")
        else:
            self.stdout.write(f"  ✓ UI_URL: {ui_url}")
        
        if not http_origin:
            warnings.append("HTTP_ORIGIN não configurado")
        else:
            self.stdout.write(f"  ✓ HTTP_ORIGIN: {http_origin}")
        
        # Verificar configurações de email
        email_backend = getattr(settings, 'EMAIL_BACKEND', None)
        if email_backend:
            self.stdout.write(f"  ✓ EMAIL_BACKEND: {email_backend}")
        else:
            warnings.append("EMAIL_BACKEND não configurado")
        
        # Verificar CSRF e Session
        csrf_origins = getattr(settings, 'CSRF_TRUSTED_ORIGINS', [])
        self.stdout.write(f"  ✓ CSRF_TRUSTED_ORIGINS: {csrf_origins}")
        
        # Verificar chave de autenticação
        authcode_key = getattr(settings, 'AUTHCODE_SECRET_KEY', None)
        if authcode_key:
            self.stdout.write("  ✓ AUTHCODE_SECRET_KEY configurado")
        else:
            errors.append("AUTHCODE_SECRET_KEY não configurado")
        
        self._show_results(errors, warnings)

    def test_badgr_app_configuration(self):
        """Testa a configuração do BadgrApp"""
        self.stdout.write(self.style.WARNING('\n2. TESTANDO CONFIGURAÇÃO DO BADGRAPP'))
        
        errors = []
        warnings = []
        
        try:
            badgr_app = BadgrApp.objects.get_current()
            self.stdout.write(f"  ✓ BadgrApp encontrado: {badgr_app.name}")
            
            # Verificar URLs de redirecionamento
            fields_to_check = [
                'email_confirmation_redirect',
                'ui_login_redirect',
                'ui_signup_success_redirect',
                'ui_connect_success_redirect'
            ]
            
            for field in fields_to_check:
                value = getattr(badgr_app, field, None)
                if value:
                    if 'https://https://' in value:
                        errors.append(f"{field} com duplo https://: {value}")
                    else:
                        self.stdout.write(f"  ✓ {field}: {value}")
                else:
                    warnings.append(f"{field} não configurado")
            
            # Verificar OAuth application
            if badgr_app.oauth_application:
                self.stdout.write(f"  ✓ OAuth Application: {badgr_app.oauth_application.name}")
            else:
                warnings.append("OAuth Application não configurado")
                
        except Exception as e:
            errors.append(f"Erro ao obter BadgrApp: {e}")
        
        self._show_results(errors, warnings)

    def test_oauth_configuration(self):
        """Testa a configuração do OAuth2"""
        self.stdout.write(self.style.WARNING('\n3. TESTANDO CONFIGURAÇÃO OAUTH2'))
        
        errors = []
        warnings = []
        
        try:
            # Verificar aplicação 'public'
            public_app = Application.objects.get(client_id='public')
            self.stdout.write(f"  ✓ Aplicação 'public' encontrada: {public_app.name}")
            
            # Verificar configurações OAuth2
            oauth_settings = getattr(settings, 'OAUTH2_PROVIDER', {})
            if oauth_settings:
                self.stdout.write("  ✓ OAUTH2_PROVIDER configurado")
                scopes = oauth_settings.get('SCOPES', {})
                self.stdout.write(f"    - Scopes disponíveis: {len(scopes)}")
            else:
                errors.append("OAUTH2_PROVIDER não configurado")
                
        except Application.DoesNotExist:
            errors.append("Aplicação OAuth2 'public' não encontrada")
        except Exception as e:
            errors.append(f"Erro na configuração OAuth2: {e}")
        
        self._show_results(errors, warnings)

    def test_allauth_configuration(self):
        """Testa a configuração do Allauth"""
        self.stdout.write(self.style.WARNING('\n4. TESTANDO CONFIGURAÇÃO ALLAUTH'))
        
        errors = []
        warnings = []
        
        # Verificar configurações do Allauth
        account_verification = getattr(settings, 'ACCOUNT_EMAIL_VERIFICATION', None)
        self.stdout.write(f"  ✓ ACCOUNT_EMAIL_VERIFICATION: {account_verification}")
        
        account_auth_method = getattr(settings, 'ACCOUNT_AUTHENTICATION_METHOD', None)
        self.stdout.write(f"  ✓ ACCOUNT_AUTHENTICATION_METHOD: {account_auth_method}")
        
        # Verificar URLs de redirecionamento do Allauth
        anon_redirect = getattr(settings, 'ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL', None)
        auth_redirect = getattr(settings, 'ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL', None)
        
        if anon_redirect:
            if 'https://https://' in anon_redirect:
                errors.append(f"ANONYMOUS_REDIRECT com duplo https://: {anon_redirect}")
            else:
                self.stdout.write(f"  ✓ ANONYMOUS_REDIRECT: {anon_redirect}")
        else:
            warnings.append("ACCOUNT_EMAIL_CONFIRMATION_ANONYMOUS_REDIRECT_URL não configurado")
        
        if auth_redirect:
            if 'https://https://' in auth_redirect:
                errors.append(f"AUTHENTICATED_REDIRECT com duplo https://: {auth_redirect}")
            else:
                self.stdout.write(f"  ✓ AUTHENTICATED_REDIRECT: {auth_redirect}")
        else:
            warnings.append("ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL não configurado")
        
        self._show_results(errors, warnings)

    def test_url_generation(self):
        """Testa a geração de URLs"""
        self.stdout.write(self.style.WARNING('\n5. TESTANDO GERAÇÃO DE URLs'))
        
        errors = []
        warnings = []
        
        try:
            # Criar uma instância da view para testar o método
            factory = RequestFactory()
            request = factory.get('/')
            view = BadgeUserEmailConfirm()
            
            # Simular BadgrApp e usuário
            badgr_app = BadgrApp.objects.get_current()
            
            # Testar método _get_safe_redirect_url
            if hasattr(view, '_get_safe_redirect_url'):
                test_redirect = view._get_safe_redirect_url(request, badgr_app, None, None)
                
                if 'https://https://' in test_redirect:
                    errors.append(f"URL gerada com duplo https://: {test_redirect}")
                else:
                    self.stdout.write(f"  ✓ URL de redirecionamento gerada: {test_redirect}")
                    
                # Verificar se a URL é válida
                try:
                    parsed = urllib.parse.urlparse(test_redirect)
                    if parsed.scheme and parsed.netloc:
                        self.stdout.write("  ✓ URL é válida")
                    else:
                        errors.append("URL gerada é inválida")
                except Exception as e:
                    errors.append(f"Erro ao analisar URL: {e}")
            else:
                errors.append("Método _get_safe_redirect_url não encontrado na view")
                
        except Exception as e:
            errors.append(f"Erro no teste de geração de URL: {e}")
        
        self._show_results(errors, warnings)

    def test_email_confirmation_view(self):
        """Testa a view de confirmação de email"""
        self.stdout.write(self.style.WARNING('\n6. TESTANDO VIEW DE CONFIRMAÇÃO'))
        
        errors = []
        warnings = []
        
        try:
            # Verificar se a view existe e tem os métodos necessários
            view = BadgeUserEmailConfirm()
            
            required_methods = ['get', '_get_safe_redirect_url']
            for method in required_methods:
                if hasattr(view, method):
                    self.stdout.write(f"  ✓ Método {method} encontrado")
                else:
                    errors.append(f"Método {method} não encontrado")
            
            # Verificar configurações de permissão
            permissions = view.permission_classes
            self.stdout.write(f"  ✓ Permission classes: {[p.__name__ for p in permissions]}")
            
            # Verificar se a view está usando BaseUserRecoveryView
            from badgeuser.api import BaseUserRecoveryView
            if isinstance(view, BaseUserRecoveryView):
                self.stdout.write("  ✓ View herda de BaseUserRecoveryView")
            else:
                warnings.append("View não herda de BaseUserRecoveryView")
                
        except Exception as e:
            errors.append(f"Erro ao testar view: {e}")
        
        self._show_results(errors, warnings)

    def test_complete_flow(self):
        """Testa o fluxo completo de confirmação"""
        self.stdout.write(self.style.WARNING('\n7. TESTANDO FLUXO COMPLETO'))
        
        errors = []
        warnings = []
        
        try:
            User = get_user_model()
            
            # Criar usuário de teste se não existir
            user, created = User.objects.get_or_create(
                email=self.test_email,
                defaults={
                    'username': self.test_email.split('@')[0],
                    'first_name': 'Teste',
                    'last_name': 'Usuario'
                }
            )
            
            if created:
                self.stdout.write(f"  ✓ Usuário de teste criado: {user.email}")
            else:
                self.stdout.write(f"  ✓ Usuário de teste encontrado: {user.email}")
            
            # Criar/verificar email address
            email_address, created = CachedEmailAddress.objects.get_or_create(
                user=user,
                email=self.test_email,
                defaults={'verified': False, 'primary': True}
            )
            
            if created:
                self.stdout.write("  ✓ EmailAddress criado")
            else:
                self.stdout.write("  ✓ EmailAddress encontrado")
            
            # Testar criação de token de confirmação
            try:
                confirmation = EmailConfirmationHMAC(email_address)
                key = confirmation.key
                self.stdout.write(f"  ✓ Token de confirmação gerado: {key[:20]}...")
                
                # Simular URL de confirmação
                confirm_url = f"/v1/user/confirmemail/{key}?token=test-token&a=1"
                self.stdout.write(f"  ✓ URL de confirmação simulada: {confirm_url}")
                
            except Exception as e:
                errors.append(f"Erro ao gerar token de confirmação: {e}")
            
            # Testar criação de AccessToken
            try:
                badgr_app = BadgrApp.objects.get_current()
                if badgr_app.oauth_application:
                    token = AccessTokenProxy.objects.generate_new_token_for_user(
                        user,
                        application=badgr_app.oauth_application,
                        scope='rw:profile rw:issuer rw:backpack'
                    )
                    self.stdout.write(f"  ✓ AccessToken criado: {token.token[:20]}...")
                else:
                    warnings.append("OAuth application não configurado no BadgrApp")
                    
            except Exception as e:
                warnings.append(f"Erro ao criar AccessToken: {e}")
                
        except Exception as e:
            errors.append(f"Erro no teste de fluxo completo: {e}")
        
        self._show_results(errors, warnings)

    def _show_results(self, errors, warnings):
        """Mostra resultados de um teste específico"""
        if errors:
            for error in errors:
                self.stdout.write(self.style.ERROR(f"  ✗ ERRO: {error}"))
        
        if warnings:
            for warning in warnings:
                self.stdout.write(self.style.WARNING(f"  ⚠ AVISO: {warning}"))
        
        if not errors and not warnings:
            self.stdout.write(self.style.SUCCESS("  ✓ Todos os testes passaram"))

    def show_final_summary(self):
        """Mostra resumo final com recomendações"""
        self.stdout.write('\nRECOMENDAÇÕES:')
        self.stdout.write('1. Se há erros de duplo https://, verifique as configurações do BadgrApp no admin')
        self.stdout.write('2. Se há problemas OAuth, verifique se a aplicação "public" existe')
        self.stdout.write('3. Se há problemas de redirecionamento, verifique UI_URL no settings')
        self.stdout.write('4. Teste o fluxo completo criando um usuário real')
        
        self.stdout.write('\nCOMANDOS ÚTEIS PARA CORREÇÃO:')
        self.stdout.write('python manage.py shell')
        self.stdout.write('from mainsite.models import BadgrApp')
        self.stdout.write('app = BadgrApp.objects.get_current()')
        self.stdout.write('app.email_confirmation_redirect = "https://badges.setic.ufsc.br/auth/welcome"')
        self.stdout.write('app.save()')
        
        self.stdout.write(f'\nPARA TESTAR FLUXO COMPLETO:')
        self.stdout.write(f'python manage.py test_email_confirmation_system --create-test-user --test-email {self.test_email}')