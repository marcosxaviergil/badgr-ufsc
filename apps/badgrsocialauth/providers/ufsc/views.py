# apps/badgrsocialauth/providers/ufsc/views.py

from allauth.socialaccount.providers.oauth2.views import (
    OAuth2Adapter,
    OAuth2CallbackView,
    OAuth2LoginView,
)
import requests
import logging

from .provider import UfscProvider


logger = logging.getLogger(__name__)


class UfscOAuth2Adapter(OAuth2Adapter):
    """Adaptador OAuth2 para UFSC"""
    provider_id = UfscProvider.id
    
    # URLs CORRETAS baseadas no projeto Tutor funcionando
    access_token_url = 'https://sistemas.ufsc.br/oauth2.0/accessToken'
    authorize_url = 'https://sistemas.ufsc.br/oauth2.0/authorize'
    profile_url = 'https://sistemas.ufsc.br/oauth2.0/profile'
    
    def complete_login(self, request, app, access_token, **kwargs):
        """Completar login após receber token"""
        logger.info("UFSC OAuth - Iniciando complete_login")
        
        try:
            headers = {
                'Authorization': f'Bearer {access_token.token}',
                'Accept': 'application/json',
            }
            
            # Buscar dados do usuário no endpoint /profile da UFSC
            resp = requests.get(self.profile_url, headers=headers, timeout=30)
            
            if resp.status_code == 200:
                user_data = resp.json()
                logger.info("UFSC OAuth - Dados recebidos com sucesso")
            else:
                logger.error(f"UFSC OAuth - Erro {resp.status_code}: {resp.text}")
                raise ValueError(f"Falha ao obter dados do usuário: {resp.status_code}")
            
            # Criar sociallogin a partir dos dados
            return self.get_provider().sociallogin_from_response(
                request, user_data
            )
            
        except Exception as e:
            logger.error(f"UFSC OAuth - Erro no complete_login: {str(e)}")
            raise


oauth2_login = OAuth2LoginView.adapter_view(UfscOAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(UfscOAuth2Adapter)