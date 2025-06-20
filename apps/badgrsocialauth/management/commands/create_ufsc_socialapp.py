# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
from django.conf import settings
import os
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Cria ou atualiza o SocialApp para UFSC OAuth'

    def handle(self, *args, **options):
        try:
            # Obter credenciais das variáveis de ambiente
            client_id = os.environ.get('SOCIAL_AUTH_UFSC_OAUTH2_KEY', 'edx-badges')
            client_secret = os.environ.get('UFSC_OAUTH_SECRET', 'sdf46sdfgsddfg')
            
            # Verificar se o provider UFSC está habilitado
            enabled_providers = os.environ.get('BADGR_SOCIAL_PROVIDERS', '').split(',')
            enabled_providers = [p.strip().lower() for p in enabled_providers if p.strip()]
            
            if 'ufsc' not in enabled_providers:
                self.stdout.write(
                    self.style.WARNING(
                        "Provider UFSC não está em BADGR_SOCIAL_PROVIDERS. "
                        "Adicionando mesmo assim..."
                    )
                )
            
            # Obter o site atual
            try:
                current_site = Site.objects.get_current()
            except Site.DoesNotExist:
                # Fallback para o primeiro site
                current_site = Site.objects.first()
                if not current_site:
                    self.stdout.write(
                        self.style.ERROR("Nenhum site configurado no Django")
                    )
                    return
            
            # Criar ou atualizar o SocialApp UFSC
            social_app, created = SocialApp.objects.get_or_create(
                provider='ufsc',
                defaults={
                    'name': 'UFSC OAuth',
                    'client_id': client_id,
                    'secret': client_secret,
                }
            )
            
            if not created:
                # Atualizar se já existe
                social_app.name = 'UFSC OAuth'
                social_app.client_id = client_id
                social_app.secret = client_secret
                social_app.save()
                
            # Associar ao site atual
            if current_site not in social_app.sites.all():
                social_app.sites.add(current_site)
                
            self.stdout.write(
                self.style.SUCCESS(
                    '{0} SocialApp UFSC OAuth com sucesso!'.format(
                        'Criado' if created else 'Atualizado'
                    )
                )
            )
            self.stdout.write('  Client ID: {0}'.format(client_id))
            self.stdout.write('  Site: {0}'.format(current_site.domain))
            
        except Exception as e:
            logger.error('Erro ao criar/atualizar SocialApp UFSC: {0}'.format(e))
            self.stdout.write(
                self.style.ERROR('Erro ao configurar SocialApp UFSC: {0}'.format(e))
            )