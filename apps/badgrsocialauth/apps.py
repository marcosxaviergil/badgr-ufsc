# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class BadgrSocialAuthConfig(AppConfig):
    name = 'badgrsocialauth'
    verbose_name = _('Badgr Social Auth')
    
    def ready(self):
        """Registrar providers customizados e aplicar patches quando Django estiver pronto"""
        # Aplicar patch para adicionar UFSC às choices do modelo SocialApp
        try:
            from allauth.socialaccount.models import SocialApp
            from django.db import models
            
            # Obter o campo provider
            provider_field = SocialApp._meta.get_field('provider')
            
            # Verificar se é um CharField com choices
            if isinstance(provider_field, models.CharField) and hasattr(provider_field, 'choices'):
                # Converter choices para lista mutável
                current_choices = list(provider_field.choices) if provider_field.choices else []
                
                # Verificar se UFSC já não está nas choices
                if not any(choice[0] == 'ufsc' for choice in current_choices):
                    # Adicionar UFSC
                    current_choices.append(('ufsc', 'UFSC'))
                    
                    # Atualizar as choices
                    provider_field.choices = current_choices
                    provider_field._choices = current_choices
                    
        except Exception:
            pass
            
        # Registrar provider UFSC
        try:
            from allauth.socialaccount import providers
            import os
            
            # Verificar se UFSC está habilitado
            enabled_providers = os.environ.get('BADGR_SOCIAL_PROVIDERS', '').split(',')
            enabled_providers = [p.strip().lower() for p in enabled_providers if p.strip()]
            
            if 'ufsc' in enabled_providers:
                from .providers.ufsc.provider import UfscProvider
                
                # Verificar se já não está registrado
                try:
                    providers.registry.by_id('ufsc')
                except LookupError:
                    providers.registry.register(UfscProvider)
                    
        except Exception:
            pass
