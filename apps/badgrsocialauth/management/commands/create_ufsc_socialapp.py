# apps/badgrsocialauth/management/commands/create_ufsc_socialapp.py

from django.core.management.base import BaseCommand
from allauth.socialaccount.models import SocialApp
from allauth.socialaccount import providers
from django.contrib.sites.models import Site
import os


class Command(BaseCommand):
    help = 'Cria ou atualiza SocialApp para OAuth UFSC'

    def handle(self, *args, **options):
        self.stdout.write('=== Configurando SocialApp UFSC ===')
        
        # ✅ Verificar se o provider UFSC está registrado
        try:
            ufsc_provider = providers.registry.by_id('ufsc')
            self.stdout.write(f'✓ Provider UFSC encontrado: {ufsc_provider.name}')
        except:
            self.stdout.write(self.style.ERROR('✗ Provider UFSC não está registrado!'))
            self.stdout.write('   Verifique se o app badgrsocialauth.providers.ufsc está em INSTALLED_APPS')
            return
        
        # ✅ Obter credenciais
        client_id = os.environ.get('UFSC_OAUTH2_CLIENT_ID', 'edx-badges')
        client_secret = os.environ.get('UFSC_OAUTH2_CLIENT_SECRET', 'sdf46sdfgsddfg')
        
        self.stdout.write(f'📋 Usando credenciais:')
        self.stdout.write(f'   Client ID: {client_id}')
        self.stdout.write(f'   Secret: {"*" * len(client_secret)}')
        
        # ✅ Obter site atual
        try:
            site = Site.objects.get_current()
            self.stdout.write(f'🌐 Site atual: {site.domain}')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erro ao obter site atual: {e}'))
            return
        
        # ✅ Criar ou atualizar SocialApp
        try:
            app, created = SocialApp.objects.get_or_create(
                provider='ufsc',
                defaults={
                    'name': 'UFSC OAuth',
                    'client_id': client_id,
                    'secret': client_secret,
                }
            )
            
            # ✅ Verificar se precisa atualizar credenciais
            needs_update = False
            if app.client_id != client_id:
                app.client_id = client_id
                needs_update = True
            if app.secret != client_secret:
                app.secret = client_secret
                needs_update = True
            
            if needs_update:
                app.save()
                self.stdout.write('🔄 Credenciais atualizadas')
            
            # ✅ Associar ao site
            app.sites.add(site)
            
            if created:
                self.stdout.write(self.style.SUCCESS('✓ SocialApp UFSC criado com sucesso'))
            else:
                self.stdout.write(self.style.WARNING('⚠ SocialApp UFSC já existia'))
            
            # ✅ Resumo final
            self.stdout.write('')
            self.stdout.write('=== Resumo da Configuração ===')
            self.stdout.write(f'📱 App: {app.name}')
            self.stdout.write(f'🔑 Client ID: {app.client_id}')
            self.stdout.write(f'🌐 Sites: {[s.domain for s in app.sites.all()]}')
            self.stdout.write(f'📍 Provider: {app.provider}')
            
            # ✅ URLs de teste
            try:
                from django.urls import reverse
                login_url = reverse('ufsc_login')
                self.stdout.write(f'🔗 URL de login: {login_url}')
            except Exception:
                self.stdout.write('⚠ URLs do provider não disponíveis ainda')
            
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('🎉 Configuração concluída!'))
            self.stdout.write('   Teste: https://api-badges.setic.ufsc.br/accounts/ufsc/login/')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'✗ Erro ao configurar SocialApp: {e}'))
            return