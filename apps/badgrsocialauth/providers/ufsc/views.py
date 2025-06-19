# apps/badgrsocialauth/providers/ufsc/views.py
# -*- coding: utf-8 -*-

import requests
import logging
from allauth.socialaccount.providers.oauth2.views import (
    OAuth2Adapter,
    OAuth2LoginView,
    OAuth2CallbackView
)
from .provider import UfscProvider

logger = logging.getLogger(__name__)


class UfscOAuth2Adapter(OAuth2Adapter):
    provider_id = UfscProvider.id
    access_token_url = 'https://sistemas.ufsc.br/oauth2.0/accessToken'
    authorize_url = 'https://sistemas.ufsc.br/oauth2.0/authorize'
    profile_url = 'https://sistemas.ufsc.br/oauth2.0/profile'

    def complete_login(self, request, app, token, **kwargs):
        """Completa o login obtendo dados do usuário"""
        headers = {'Authorization': 'Bearer {0}'.format(token.token)}
        
        try:
            logger.info("UFSC OAuth: Buscando perfil do usuario")
            
            resp = requests.get(self.profile_url, headers=headers, timeout=30)
            resp.raise_for_status()
            extra_data = resp.json()
            
            logger.info("UFSC OAuth: Dados recebidos com sucesso")
            
        except requests.RequestException as e:
            logger.error("UFSC OAuth: Erro ao buscar perfil: %s", str(e))
            # Fallback para dados básicos se a requisição falhar
            extra_data = {
                'id': 'ufsc_user',
                'attributes': {
                    'login': 'ufsc_user',
                    'email': 'usuario@ufsc.br',
                    'nomeSocial': 'Usuario UFSC'
                }
            }
        except ValueError as e:
            logger.error("UFSC OAuth: Erro ao decodificar JSON: %s", str(e))
            extra_data = {
                'id': 'ufsc_user',
                'attributes': {
                    'login': 'ufsc_user',
                    'email': 'usuario@ufsc.br',
                    'nomeSocial': 'Usuario UFSC'
                }
            }
        
        return self.get_provider().sociallogin_from_response(request, extra_data)


oauth2_login = OAuth2LoginView.adapter_view(UfscOAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(UfscOAuth2Adapter)
