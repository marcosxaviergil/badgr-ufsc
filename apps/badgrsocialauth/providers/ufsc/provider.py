# apps/badgrsocialauth/providers/ufsc/provider.py

from allauth.socialaccount import providers
from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider


class UfscAccount(ProviderAccount):
    def to_str(self):
        attributes = self.account.extra_data.get('attributes', {})
        return (attributes.get('nomeSocial') or
                attributes.get('nome') or
                attributes.get('personName') or
                super(UfscAccount, self).to_str())


class UfscProvider(OAuth2Provider):
    id = 'ufsc'
    name = 'UFSC'
    account_class = UfscAccount

    def extract_uid(self, data):
        """Extrai ID único do usuário"""
        attributes = data.get('attributes', {})
        return str(attributes.get('login') or
                   attributes.get('idPessoa') or
                   data.get('id', 'ufsc_user'))

    def extract_common_fields(self, data):
        """Extrai campos comuns para criar/atualizar usuário"""
        attributes = data.get('attributes', {})

        # Nome completo usando nomeSocial como prioridade
        nome_completo = (attributes.get('nomeSocial') or
                         attributes.get('nome') or
                         attributes.get('personName') or '')

        nome_parts = nome_completo.strip().split(' ') if nome_completo else []
        first_name = nome_parts[0] if nome_parts else ''
        last_name = ' '.join(nome_parts[1:]) if len(nome_parts) > 1 else ''

        # Email sem validação
        email = attributes.get('email', 'usuario@ufsc.br')
        
        # Username baseado no login
        username = attributes.get('login', '')
        if not username:
            username = email.split('@')[0] if '@' in email else 'usuario_ufsc'

        return dict(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
        )

    def get_default_scope(self):
        return ['openid', 'profile', 'email']


# REMOVIDO: providers.registry.register(UfscProvider)
# O registro agora é feito no apps.py no método ready() para evitar
# o warning "Apps aren't loaded yet"