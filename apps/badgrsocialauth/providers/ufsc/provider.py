# apps/badgrsocialauth/providers/ufsc/provider.py

from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider


class UfscAccount(ProviderAccount):
    def to_str(self):
        attributes = self.account.extra_data.get('attributes', {})
        return (attributes.get('nomeSocial') or
                attributes.get('nome') or
                str(self.account.extra_data.get('id', 'Usuario UFSC')))


class UfscProvider(OAuth2Provider):
    id = 'ufsc'
    name = 'UFSC'
    account_class = UfscAccount

    def extract_uid(self, data):
        attributes = data.get('attributes', {})
        return str(attributes.get('login') or data.get('id', 'ufsc_user'))

    def extract_common_fields(self, data):
        attributes = data.get('attributes', {})
        
        nome_completo = (attributes.get('nomeSocial') or
                         attributes.get('nome') or 'Usuario UFSC')
        
        nome_parts = nome_completo.strip().split(' ') if nome_completo else ['Usuario', 'UFSC']
        first_name = nome_parts[0] if nome_parts else 'Usuario'
        last_name = ' '.join(nome_parts[1:]) if len(nome_parts) > 1 else 'UFSC'
        
        email = attributes.get('email', 'usuario@ufsc.br')
        username = attributes.get('login', 'ufsc_user')
        
        if not username or username.isdigit():
            username = email.split('@')[0] if '@' in email else 'ufsc_user'

        return {
            'username': str(username).lower(),
            'email': str(email).lower(),
            'first_name': str(first_name),
            'last_name': str(last_name),
        }

    def get_default_scope(self):
        return ['openid', 'profile', 'email']
