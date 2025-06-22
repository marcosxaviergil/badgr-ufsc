# apps/badgrsocialauth/providers/ufsc/provider.py

from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider
from badgeuser.models import CachedEmailAddress


class UfscAccount(ProviderAccount):
    """Conta de usuário UFSC"""
    pass


class UfscProvider(OAuth2Provider):
    """
    Provider OAuth2 para UFSC
    Configurado para ser selecionado manualmente no admin
    """
    id = 'ufsc'
    name = 'UFSC'
    package = 'badgrsocialauth.providers.ufsc'
    account_class = UfscAccount
    
    def get_default_scope(self):
        return ['openid', 'profile', 'email']
    
    def extract_uid(self, data):
        """Extrair ID único do usuário"""
        return data.get('sub') or data.get('login') or data.get('id')
    
    def extract_common_fields(self, data):
        """Mapear campos do OAuth para usuário Django"""
        return {
            'username': data.get('login'),
            'email': data.get('email'),
            'first_name': data.get('nomeSocial', '').split()[0] if data.get('nomeSocial') else '',
            'last_name': ' '.join(data.get('nomeSocial', '').split()[1:]) if data.get('nomeSocial') else '',
        }
    
    def extract_email_addresses(self, data):
        """Extrair endereços de email verificados"""
        email = data.get('email')
        if email:
            return [CachedEmailAddress(
                email=email, 
                verified=True, 
                primary=True
            )]
        return []
