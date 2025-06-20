# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from allauth.socialaccount import providers
from allauth.socialaccount.models import SocialApp
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Testa a configuração do UFSC OAuth'

    def handle(self, *args, **options):
        self.stdout.write("=== Teste de Configuração UFSC OAuth ===\n")
        
        # 0. Verificar variáveis de ambiente
        self.stdout.write("=== Variáveis de Ambiente ===")
        client_key = os.environ.get('SOCIAL_AUTH_UFSC_OAUTH2_KEY')
        secret_key = os.environ.get('UFSC_OAUTH_SECRET')
        social_providers = os.environ.get('BADGR_SOCIAL_PROVIDERS', '')
        
        self.stdout.write('SOCIAL_AUTH_UFSC_OAUTH2_KEY: {0}'.format(
            client_key if client_key else 'NÃO DEFINIDA'
        ))
        self.stdout.write('UFSC_OAUTH_SECRET: {0}'.format(
            '***' if secret_key else 'NÃO DEFINIDA'
        ))
        self.stdout.write('BADGR_SOCIAL_PROVIDERS: {0}'.format(
            social_providers if social_providers else 'NÃO DEFINIDA'
        ))
        
        # Verificar se UFSC está nos providers habilitados
        enabled_providers = social_providers.split(',')
        enabled_providers = [p.strip().lower() for p in enabled_providers if p.strip()]
        
        if 'ufsc' in enabled_providers:
            self.stdout.write(self.style.SUCCESS("✓ UFSC está em BADGR_SOCIAL_PROVIDERS"))
        else:
            self.stdout.write(self.style.WARNING("⚠ UFSC não está em BADGR_SOCIAL_PROVIDERS"))
            self.stdout.write("  Providers habilitados: {0}".format(', '.join(enabled_providers)))
        
        self.stdout.write("")
        
        # 1. Verificar se o provider está registrado
        try:
            provider = providers.registry.by_id('ufsc')
            self.stdout.write(
                self.style.SUCCESS('✓ Provider UFSC registrado: {0}'.format(provider.name))
            )
        except LookupError as e:
            self.stdout.write(
                self.style.ERROR('✗ Provider UFSC não registrado: {0}'.format(e))
            )
            return
            
        # 2. Verificar se existe SocialApp configurado
        try:
            social_app = SocialApp.objects.get(provider='ufsc')
            self.stdout.write(
                self.style.SUCCESS('✓ SocialApp UFSC encontrado: {0}'.format(social_app.name))
            )
            self.stdout.write('  Client ID: {0}'.format(social_app.client_id))
            
            sites = social_app.sites.all()
            if sites:
                self.stdout.write('  Sites associados: {0}'.format(
                    ', '.join([s.domain for s in sites])
                ))
            else:
                self.stdout.write(self.style.WARNING('  ⚠ Nenhum site associado'))
            
            # Verificar se as credenciais batem com as variáveis de ambiente
            expected_client_id = os.environ.get('SOCIAL_AUTH_UFSC_OAUTH2_KEY', 'edx-badges')
            if social_app.client_id == expected_client_id:
                self.stdout.write(self.style.SUCCESS("  ✓ Client ID corresponde à variável de ambiente"))
            else:
                self.stdout.write(self.style.WARNING(
                    '  ⚠ Client ID difere da variável de ambiente: {0}'.format(expected_client_id)
                ))
                
        except SocialApp.DoesNotExist:
            self.stdout.write(
                self.style.ERROR("✗ SocialApp UFSC não configurado no banco de dados")
            )
            
        # 3. Verificar configurações no settings
        if hasattr(settings, 'SOCIALACCOUNT_PROVIDERS'):
            providers_config = getattr(settings, 'SOCIALACCOUNT_PROVIDERS', {})
            if 'ufsc' in providers_config:
                self.stdout.write(
                    self.style.SUCCESS("✓ Configurações UFSC encontradas em SOCIALACCOUNT_PROVIDERS")
                )
                ufsc_config = providers_config.get('ufsc', {})
                if 'APP' in ufsc_config:
                    self.stdout.write("  Configuração APP presente no settings")
            else:
                self.stdout.write(
                    self.style.WARNING("⚠ UFSC não configurado em SOCIALACCOUNT_PROVIDERS")
                )
        else:
            self.stdout.write(
                self.style.WARNING("⚠ SOCIALACCOUNT_PROVIDERS não definido nas configurações")
            )
            
        # 4. Listar todos os providers registrados
        self.stdout.write("\n=== Providers Registrados ===")
        try:
            provider_map = providers.registry.provider_map
            for provider_id, provider_class in provider_map.items():
                self.stdout.write('- {0}: {1}'.format(provider_id, provider_class.name))
        except AttributeError:
            # Fallback para versão mais antiga
            self.stdout.write("  (lista de providers não disponível)")
            
        # 5. URLs de callback
        self.stdout.write("\n=== URLs OAuth ===")
        self.stdout.write("Login URL: /accounts/ufsc/login/")
        self.stdout.write("Callback URL: /accounts/ufsc/login/callback/")
        self.stdout.write("URL completa de callback para configurar no servidor UFSC:")
        ui_url = os.environ.get('UI_URL', 'https://badges.setic.ufsc.br')
        self.stdout.write("  {0}/accounts/ufsc/login/callback/".format(ui_url))