# apps/mainsite/management/commands/setup_initial_data.py

from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import transaction
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from oauth2_provider.models import Application
from mainsite.models import BadgrApp, ApplicationInfo
import os


class Command(BaseCommand):
    help = 'Configura dados iniciais do sistema Badgr UFSC (BadgrApp, OAuth)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force-recreate',
            action='store_true',
            help='Forçar recriação de todos os dados iniciais',
        )

    def handle(self, *args, **options):
        force_recreate = options.get('force_recreate', False)
        
        self.stdout.write(
            self.style.SUCCESS('🚀 Iniciando configuração dos dados iniciais do Badgr UFSC...\n')
        )

        try:
            with transaction.atomic():
                # 1. Configurar Sites Django
                self._setup_sites(force_recreate)
                
                # 2. Configurar BadgrApp
                self._setup_badgrapp(force_recreate)
                
                # 3. Configurar OAuth2 Applications
                self._setup_oauth_applications(force_recreate)
                
                # 4. Configurar SocialApp UFSC
                self._setup_socialapp_ufsc(force_recreate)
                
                # 5. Configurar External Tools (removido por enquanto devido a campos incompatíveis)
                # self._setup_external_tools(force_recreate)
                
                self.stdout.write(
                    self.style.SUCCESS('\n✅ Configuração inicial concluída com sucesso!')
                )
                
                # 6. Resumo final
                self._show_summary()
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n❌ Erro durante configuração: {str(e)}')
            )
            raise

    def _get_base_url(self):
        """Obter URL base das variáveis de ambiente"""
        ui_url = os.environ.get('UI_URL', 'https://badges.setic.ufsc.br')
        # Remover trailing slash se existir
        return ui_url.rstrip('/')

    def _get_domain(self):
        """Extrair domínio da URL base"""
        base_url = self._get_base_url()
        # Remover protocolo para obter apenas o domínio
        domain = base_url.replace('https://', '').replace('http://', '')
        return domain

    def _setup_sites(self, force_recreate):
        """Configurar Sites Django"""
        self.stdout.write('📍 Configurando Sites Django...')
        
        domain = self._get_domain()
        
        # Site principal (usando variável de ambiente)
        site, created = Site.objects.get_or_create(
            id=1,
            defaults={
                'domain': domain,
                'name': 'Badgr UFSC'
            }
        )
        
        if not created and (force_recreate or site.domain != domain):
            site.domain = domain
            site.name = 'Badgr UFSC'
            site.save()
            
        action = 'criado' if created else ('atualizado' if force_recreate else 'já existe')
        self.stdout.write(f'  ✓ Site principal {action}: {site.domain}')
        
        # Site API (opcional)
        api_domain = f"api-{domain}" if not domain.startswith('api-') else domain
        api_site, api_created = Site.objects.get_or_create(
            domain=api_domain,
            defaults={'name': 'Badgr UFSC API'}
        )
        
        action = 'criado' if api_created else 'já existe'
        self.stdout.write(f'  ✓ Site API {action}: {api_site.domain}')

    def _setup_badgrapp(self, force_recreate):
        """Configurar BadgrApp principal"""
        self.stdout.write('\n🏠 Configurando BadgrApp...')
        
        base_url = self._get_base_url()
        domain = self._get_domain()
        
        # Deletar localhost:81 se existir
        try:
            localhost_app = BadgrApp.objects.get(cors='localhost:81')
            localhost_app.delete()
            self.stdout.write('  🗑️ BadgrApp localhost:81 removido')
        except BadgrApp.DoesNotExist:
            pass

        # Configurar BadgrApp principal usando variáveis de ambiente
        badgr_app, created = BadgrApp.objects.get_or_create(
            cors=domain,
            defaults={
                'name': 'Badgr UFSC',
                'is_default': True,
                'signup_redirect': f'{base_url}/signup/',
                'email_confirmation_redirect': f'{base_url}/auth/login/',
                'forgot_password_redirect': f'{base_url}/change-password/',
                'ui_login_redirect': f'{base_url}/auth/login/',
                'ui_signup_success_redirect': f'{base_url}/recipient/',
                'ui_signup_failure_redirect': f'{base_url}/auth/login/?error=signup_failed',
                'ui_connect_success_redirect': f'{base_url}/profile/',
                'public_pages_redirect': f'{base_url}/public/',
                'oauth_authorization_redirect': f'{base_url}/auth/oauth2/authorize/'
            }
        )

        if not created and (force_recreate or not badgr_app.is_default):
            # Atualizar configurações usando variáveis de ambiente
            badgr_app.name = 'Badgr UFSC'
            badgr_app.is_default = True
            badgr_app.signup_redirect = f'{base_url}/signup/'
            badgr_app.email_confirmation_redirect = f'{base_url}/auth/login/'
            badgr_app.forgot_password_redirect = f'{base_url}/change-password/'
            badgr_app.ui_login_redirect = f'{base_url}/auth/login/'
            badgr_app.ui_signup_success_redirect = f'{base_url}/recipient/'
            badgr_app.ui_signup_failure_redirect = f'{base_url}/auth/login/?error=signup_failed'
            badgr_app.ui_connect_success_redirect = f'{base_url}/profile/'
            badgr_app.public_pages_redirect = f'{base_url}/public/'
            badgr_app.oauth_authorization_redirect = f'{base_url}/auth/oauth2/authorize/'
            badgr_app.save()

        action = 'criado' if created else 'atualizado'
        self.stdout.write(f'  ✓ BadgrApp {action}: {badgr_app.cors} (ID: {badgr_app.id})')
        self.stdout.write(f'    Base URL: {base_url}')

    def _setup_oauth_applications(self, force_recreate):
        """Configurar OAuth2 Applications"""
        self.stdout.write('\n🔐 Configurando OAuth2 Applications...')
        
        # Application "public" padrão
        public_app, created = Application.objects.get_or_create(
            client_id='public',
            defaults={
                'name': 'Badgr Public Default',
                'client_type': Application.CLIENT_PUBLIC,
                'authorization_grant_type': Application.GRANT_PASSWORD,
            }
        )
        
        action = 'criado' if created else 'já existe'
        self.stdout.write(f'  ✓ Application Public {action}: {public_app.client_id}')
        
        # ApplicationInfo para public
        app_info, info_created = ApplicationInfo.objects.get_or_create(
            application=public_app,
            defaults={
                'name': 'Badgr Public API',
                'allowed_scopes': 'rw:profile rw:issuer rw:backpack'
            }
        )
        
        if not info_created and force_recreate:
            app_info.allowed_scopes = 'rw:profile rw:issuer rw:backpack'
            app_info.save()
            
        action = 'criado' if info_created else ('atualizado' if force_recreate else 'já existe')
        self.stdout.write(f'  ✓ ApplicationInfo {action} para public')

    def _setup_socialapp_ufsc(self, force_recreate):
        """Configurar SocialApp UFSC OAuth"""
        self.stdout.write('\n🎓 Configurando SocialApp UFSC...')
        
        # Verificar se UFSC está habilitado
        badgr_providers = os.environ.get('BADGR_SOCIAL_PROVIDERS', '').split(',')
        badgr_providers = [p.strip().lower() for p in badgr_providers if p.strip()]
        
        if 'ufsc' not in badgr_providers:
            self.stdout.write('  ⚠️ UFSC não está em BADGR_SOCIAL_PROVIDERS, pulando configuração')
            return
        
        try:
            # Buscar site usando domínio das variáveis de ambiente
            domain = self._get_domain()
            site = Site.objects.get(domain=domain)
            
            # Configurar SocialApp UFSC
            ufsc_app, created = SocialApp.objects.get_or_create(
                provider='ufsc',
                defaults={
                    'name': 'UFSC OAuth',
                    'client_id': os.environ.get('SOCIAL_AUTH_UFSC_OAUTH2_KEY', 'edx-badges'),
                    'secret': os.environ.get('UFSC_OAUTH_SECRET', 'sdf46sdfgsddfg'),
                }
            )
            
            # Associar ao site correto
            if site not in ufsc_app.sites.all():
                ufsc_app.sites.add(site)
                
            # Atualizar configurações se necessário
            if not created and force_recreate:
                ufsc_app.client_id = os.environ.get('SOCIAL_AUTH_UFSC_OAUTH2_KEY', 'edx-badges')
                ufsc_app.secret = os.environ.get('UFSC_OAUTH_SECRET', 'sdf46sdfgsddfg')
                ufsc_app.save()
            
            action = 'criado' if created else ('atualizado' if force_recreate else 'já existe')
            self.stdout.write(f'  ✓ SocialApp UFSC {action}: {ufsc_app.client_id}')
            self.stdout.write(f'    Sites: {", ".join([s.domain for s in ufsc_app.sites.all()])}')
            
        except Site.DoesNotExist:
            self.stdout.write(f'  ❌ Site {domain} não encontrado. Execute novamente a configuração de sites.')

    def _show_summary(self):
        """Mostrar resumo da configuração"""
        self.stdout.write('\n📋 Resumo da Configuração:')
        
        base_url = self._get_base_url()
        domain = self._get_domain()
        
        self.stdout.write(f'  🌐 Domínio principal: {domain}')
        self.stdout.write(f'  🔗 URL base: {base_url}')
        
        # BadgrApps
        self.stdout.write('\n📱 BadgrApps:')
        for app in BadgrApp.objects.all():
            default_mark = ' [PADRÃO]' if app.is_default else ''
            self.stdout.write(f'  - ID {app.id}: {app.cors}{default_mark}')
        
        # OAuth Applications
        self.stdout.write('\n🔐 OAuth Applications:')
        for app in Application.objects.all():
            self.stdout.write(f'  - {app.name}: {app.client_id}')
        
        # SocialApps
        self.stdout.write('\n🎓 Social Apps:')
        for social_app in SocialApp.objects.all():
            sites = ", ".join([s.domain for s in social_app.sites.all()])
            self.stdout.write(f'  - {social_app.provider}: {social_app.name} (Sites: {sites})')
        
        self.stdout.write(f'\n📍 URLs OAuth configuradas para: {base_url}')
        self.stdout.write(f'  - Login URL: {base_url}/accounts/ufsc/login/')
        self.stdout.write(f'  - Callback URL: {base_url}/accounts/ufsc/login/callback/')
