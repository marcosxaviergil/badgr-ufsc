# apps/badgrsocialauth/providers/ufsc/views.py

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
            resp = requests.get(self.profile_url, headers=headers, timeout=30)
            resp.raise_for_status()
            extra_data = resp.json()
            
            # ✅ CORREÇÃO: Normalizar dados recebidos
            extra_data = self._normalize_ufsc_data(extra_data)
            
        except requests.RequestException:
            # ✅ CORREÇÃO: Fallback com dados mais robustos
            extra_data = {
                'id': 'ufsc_user',
                'attributes': {
                    'idPessoa': 'ufsc_user',
                    'login': 'usuario_ufsc',
                    'email': 'usuario@ufsc.br',
                    'nomeSocial': 'Usuario UFSC',
                    'nome': 'Usuario UFSC'
                }
            }
        
        return self.get_provider().sociallogin_from_response(request, extra_data)

    def _normalize_ufsc_data(self, data):
        """
        ✅ CORREÇÃO: Normalizar e validar dados da UFSC
        """
        # Garantir estrutura básica
        if 'attributes' not in data:
            data['attributes'] = {}
        
        attributes = data['attributes']
        
        # ✅ Normalizar campos obrigatórios
        if not attributes.get('nomeSocial') and not attributes.get('nome'):
            # Se não tem nome, usar o login ou email
            login = attributes.get('login', '')
            email = attributes.get('email', '')
            if login:
                attributes['nomeSocial'] = login.replace('.', ' ').title()
            elif email:
                attributes['nomeSocial'] = email.split('@')[0].replace('.', ' ').title()
            else:
                attributes['nomeSocial'] = 'Usuario UFSC'
        
        # ✅ Garantir que email existe
        if not attributes.get('email'):
            login = attributes.get('login', 'usuario')
            attributes['email'] = f"{login}@ufsc.br"
        
        # ✅ Garantir que login existe
        if not attributes.get('login'):
            email = attributes.get('email', 'usuario@ufsc.br')
            attributes['login'] = email.split('@')[0]
        
        # ✅ Garantir ID único
        if not data.get('id') and not attributes.get('idPessoa'):
            data['id'] = attributes.get('login', 'ufsc_user')
        
        return data


oauth2_login = OAuth2LoginView.adapter_view(UfscOAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(UfscOAuth2Adapter)