# apps/badgrsocialauth/providers/ufsc/provider.py

from allauth.socialaccount import providers
from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider


class UfscAccount(ProviderAccount):
    def to_str(self):
        """
        Define como o nome da conta será exibido na interface
        """
        attributes = self.account.extra_data.get('attributes', {})
        
        # ✅ CORREÇÃO: Priorizar nomeSocial e ter fallbacks robustos
        display_name = (
            attributes.get('nomeSocial') or
            attributes.get('nome') or 
            attributes.get('personName') or
            attributes.get('login') or
            'Usuário UFSC'
        )
        
        return display_name.strip() if display_name else 'Usuário UFSC'


class UfscProvider(OAuth2Provider):
    id = 'ufsc'
    name = 'UFSC'
    account_class = UfscAccount

    def extract_uid(self, data):
        """Extrai ID único do usuário"""
        attributes = data.get('attributes', {})
        
        # ✅ CORREÇÃO: Usar idPessoa como UID principal
        uid = (
            attributes.get('idPessoa') or
            attributes.get('login') or
            data.get('id') or
            'ufsc_unknown'
        )
        
        return str(uid)

    def extract_common_fields(self, data):
        """
        ✅ CORREÇÃO PRINCIPAL: Mapeamento robusto dos campos UFSC
        """
        attributes = data.get('attributes', {})

        # ✅ Nome completo com fallbacks robustos
        nome_completo = (
            attributes.get('nomeSocial') or
            attributes.get('nome') or
            attributes.get('personName') or
            ''
        ).strip()

        # ✅ Separar nome em partes
        if nome_completo:
            nome_parts = nome_completo.split(' ')
            first_name = nome_parts[0] if nome_parts else 'Usuario'
            last_name = ' '.join(nome_parts[1:]) if len(nome_parts) > 1 else 'UFSC'
        else:
            first_name = 'Usuario'
            last_name = 'UFSC'

        # ✅ Email com fallback
        email = attributes.get('email') or 'usuario@ufsc.br'
        
        # ✅ Username baseado no login
        username = attributes.get('login') or email.split('@')[0] or 'usuario_ufsc'

        # ✅ CORREÇÃO: Garantir que nenhum campo seja None
        return {
            'username': str(username).strip() if username else 'usuario_ufsc',
            'email': str(email).strip() if email else 'usuario@ufsc.br',
            'first_name': str(first_name).strip() if first_name else 'Usuario',
            'last_name': str(last_name).strip() if last_name else 'UFSC',
        }

    def get_default_scope(self):
        return ['openid', 'profile', 'email']

    def sociallogin_from_response(self, request, response):
        """
        ✅ CORREÇÃO: Pré-processar dados antes de criar sociallogin
        """
        # Garantir que attributes existe
        if 'attributes' not in response:
            response['attributes'] = {}
        
        # Normalizar campos vazios
        attributes = response['attributes']
        for field in ['nomeSocial', 'nome', 'personName', 'email', 'login']:
            if field in attributes and not attributes[field]:
                del attributes[field]
        
        sociallogin = super().sociallogin_from_response(request, response)
        
        # ✅ Garantir que o usuário tenha dados válidos
        if sociallogin.user:
            if not sociallogin.user.first_name:
                sociallogin.user.first_name = 'Usuario'
            if not sociallogin.user.last_name:
                sociallogin.user.last_name = 'UFSC'
            if not sociallogin.user.email:
                sociallogin.user.email = 'usuario@ufsc.br'
                
        return sociallogin