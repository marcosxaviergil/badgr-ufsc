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
        return str(attributes.get('idPessoa') or
                   attributes.get('login') or
                   data.get('id', 'ufsc_user'))

    def extract_common_fields(self, data):
        """Extrai campos comuns para criar/atualizar usuário"""
        attributes = data.get('attributes', {})

        # Nome completo usando nomeSocial como prioridade
        nome_completo = (attributes.get('nomeSocial') or
                         attributes.get('nome') or
                         attributes.get('personName') or '')

        nome_parts = nome_completo.strip().split(' ') if nome_completo else []
        first_name = nome_parts[0] if nome_parts else 'Usuario'
        last_name = ' '.join(nome_parts[1:]) if len(nome_parts) > 1 else 'UFSC'

        # Email sem validação - usar direto do servidor OAuth
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

    def sociallogin_from_response(self, request, response):
        """
        ✅ CORREÇÃO: Criar SocialLogin e marcar email como verificado automaticamente
        """
        sociallogin = super(UfscProvider, self).sociallogin_from_response(request, response)
        
        # ✅ AUTO-VERIFICAR EMAIL para usuários UFSC
        if sociallogin.user and sociallogin.user.email:
            from allauth.account.models import EmailAddress
            
            # Limpar emails anteriores
            sociallogin.email_addresses = []
            
            # Criar email verificado
            email_address = EmailAddress(
                email=sociallogin.user.email,
                verified=True,  # ✅ MARCAR COMO VERIFICADO
                primary=True
            )
            sociallogin.email_addresses = [email_address]
            
            # ✅ GARANTIR QUE sociallogin.state seja definido
            sociallogin.state = {
                'provider': 'ufsc',
                'process': 'login'
            }
        
        return sociallogin