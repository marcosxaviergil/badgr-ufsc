# apps/badgrsocialauth/providers/ufsc/views.py

from allauth.socialaccount.providers.oauth2.views import (
    OAuth2Adapter,
    OAuth2CallbackView,
    OAuth2LoginView,
)

from .provider import UfscProvider


class UfscOAuth2Adapter(OAuth2Adapter):
    """Adaptador OAuth2 para UFSC"""
    provider_id = UfscProvider.id
    
    # URLs do servidor OAuth UFSC
    access_token_url = 'https://sistemas.ufsc.br/oauth2/token'
    authorize_url = 'https://sistemas.ufsc.br/oauth2/authorize'
    profile_url = 'https://sistemas.ufsc.br/oauth2/userinfo'
    
    def complete_login(self, request, app, access_token, **kwargs):
        """Completar login após receber token"""
        import requests
        
        headers = {'Authorization': f'Bearer {access_token.token}'}
        resp = requests.get(self.profile_url, headers=headers)
        resp.raise_for_status()
        
        return self.get_provider().sociallogin_from_response(
            request, resp.json()
        )


oauth2_login = OAuth2LoginView.adapter_view(UfscOAuth2Adapter)
oauth2_callback = OAuth2CallbackView.adapter_view(UfscOAuth2Adapter)