# apps/mainsite/management/commands/test_local_login.py

from django.core.management.base import BaseCommand
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.backends import ModelBackend
from allauth.account.auth_backends import AuthenticationBackend
from django.contrib.sites.models import Site
from django.conf import settings
import json


class Command(BaseCommand):
    help = 'Testa configuração de login local'

    def add_arguments(self, parser):
        parser.add_argument('--email', type=str, help='Email para teste')
        parser.add_argument('--password', type=str, help='Senha para teste')
        parser.add_argument('--create-user', action='store_true', help='Criar usuário de teste')

    def handle(self, *args, **options):
        self.stdout.write("=== DIAGNÓSTICO DE LOGIN LOCAL ===\n")
        
        # 1. Verificar configurações Django
        self.stdout.write("1. Configurações Django:")
        self.stdout.write(f"   AUTHENTICATION_BACKENDS: {settings.AUTHENTICATION_BACKENDS}")
        self.stdout.write(f"   ACCOUNT_AUTHENTICATION_METHOD: {getattr(settings, 'ACCOUNT_AUTHENTICATION_METHOD', 'Não definido')}")
        self.stdout.write(f"   ACCOUNT_EMAIL_VERIFICATION: {getattr(settings, 'ACCOUNT_EMAIL_VERIFICATION', 'Não definido')}")
        self.stdout.write(f"   ACCOUNT_EMAIL_REQUIRED: {getattr(settings, 'ACCOUNT_EMAIL_REQUIRED', 'Não definido')}")
        self.stdout.write(f"   SOCIALACCOUNT_AUTO_SIGNUP: {getattr(settings, 'SOCIALACCOUNT_AUTO_SIGNUP', 'Não definido')}")
        
        # 2. Verificar backends disponíveis
        self.stdout.write("\n2. Backends de autenticação:")
        for backend in settings.AUTHENTICATION_BACKENDS:
            try:
                module_path, class_name = backend.rsplit('.', 1)
                module = __import__(module_path, fromlist=[class_name])
                backend_class = getattr(module, class_name)
                self.stdout.write(f"   ✓ {backend} - {backend_class}")
            except Exception as e:
                self.stdout.write(f"   ✗ {backend} - ERRO: {e}")
        
        # 3. Verificar Site
        self.stdout.write("\n3. Configuração de Sites:")
        try:
            site = Site.objects.get_current()
            self.stdout.write(f"   Site atual: {site.domain} ({site.name})")
        except Exception as e:
            self.stdout.write(f"   ✗ Erro no site: {e}")
        
        # 4. Teste de usuário (se fornecido)
        email = options.get('email')
        password = options.get('password')
        
        if options.get('create_user') and email and password:
            self.create_test_user(email, password)
        
        if email and password:
            self.test_authentication(email, password)
        
        # 5. Verificar usuários existentes
        self.stdout.write("\n5. Usuários no banco:")
        User = get_user_model()
        users = User.objects.all()[:5]
        for user in users:
            self.stdout.write(f"   - {user.email} (ativo: {user.is_active})")
        
        self.stdout.write(f"\n   Total de usuários: {User.objects.count()}")

    def create_test_user(self, email, password):
        self.stdout.write("\n4. Criando usuário de teste...")
        User = get_user_model()
        
        try:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email.split('@')[0],
                    'first_name': 'Teste',
                    'last_name': 'Local',
                    'is_active': True
                }
            )
            
            if created:
                user.set_password(password)
                user.save()
                self.stdout.write(f"   ✓ Usuário criado: {email}")
            else:
                user.set_password(password)
                user.save()
                self.stdout.write(f"   ✓ Senha atualizada para usuário existente: {email}")
            
            # Verificar CachedEmailAddress se existe
            try:
                from badgeuser.models import CachedEmailAddress
                email_obj, created = CachedEmailAddress.objects.get_or_create(
                    email=email,
                    defaults={
                        'user': user,
                        'verified': True,
                        'primary': True
                    }
                )
                if created:
                    self.stdout.write(f"   ✓ CachedEmailAddress criado para {email}")
                else:
                    email_obj.verified = True
                    email_obj.save()
                    self.stdout.write(f"   ✓ CachedEmailAddress verificado para {email}")
            except ImportError:
                self.stdout.write("   ⚠ CachedEmailAddress não disponível")
                
        except Exception as e:
            self.stdout.write(f"   ✗ Erro ao criar usuário: {e}")

    def test_authentication(self, email, password):
        self.stdout.write(f"\n6. Testando autenticação para {email}:")
        
        # Teste direto do Django
        self.stdout.write("   a) Autenticação direta do Django:")
        user_django = authenticate(username=email, password=password)
        if user_django:
            self.stdout.write(f"      ✓ Django auth: {user_django}")
        else:
            self.stdout.write("      ✗ Django auth: FALHOU")
        
        # Teste específico do ModelBackend
        self.stdout.write("   b) Teste específico ModelBackend:")
        backend = ModelBackend()
        user_model = backend.authenticate(None, username=email, password=password)
        if user_model:
            self.stdout.write(f"      ✓ ModelBackend: {user_model}")
        else:
            self.stdout.write("      ✗ ModelBackend: FALHOU")
        
        # Teste específico do AllAuth
        self.stdout.write("   c) Teste específico AllAuth:")
        try:
            auth_backend = AuthenticationBackend()
            user_allauth = auth_backend.authenticate(None, username=email, password=password)
            if user_allauth:
                self.stdout.write(f"      ✓ AllAuth: {user_allauth}")
            else:
                self.stdout.write("      ✗ AllAuth: FALHOU")
        except Exception as e:
            self.stdout.write(f"      ✗ AllAuth: ERRO - {e}")
        
        # Verificar se usuário existe
        User = get_user_model()
        try:
            user = User.objects.get(email=email)
            self.stdout.write(f"   d) Usuário existe: {user} (ativo: {user.is_active})")
            
            # Verificar senha
            if user.check_password(password):
                self.stdout.write("      ✓ Senha correta")
            else:
                self.stdout.write("      ✗ Senha incorreta")
                
        except User.DoesNotExist:
            self.stdout.write("   ✗ Usuário não existe")
        except Exception as e:
            self.stdout.write(f"   ✗ Erro: {e}")
