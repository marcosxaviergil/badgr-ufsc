# apps/badgrsocialauth/providers/ufsc/provider.py

from allauth.socialaccount import providers
from allauth.socialaccount.providers.base import ProviderAccount
from allauth.socialaccount.providers.oauth2.provider import OAuth2Provider
from badgeuser.models import CachedEmailAddress
import logging


logger = logging.getLogger(__name__)


class UfscAccount(ProviderAccount):
    """Conta de usuário UFSC"""
    pass


class UfscProvider(OAuth2Provider):
    """
    Provider OAuth2 para UFSC
    ✅ CORREÇÃO: Estrutura idêntica aos providers funcionais (kony/twitter)
    """
    id = 'ufsc'
    name = 'UFSC'
    account_class = UfscAccount
    
    def get_default_scope(self):
        return ['openid', 'profile', 'email']
    
    def extract_uid(self, data):
        """Extrair ID único do usuário"""
        # Tentar campo 'id' primeiro, depois 'idPessoa' dos attributes
        uid = data.get('id')
        if not uid:
            attributes = data.get('attributes', {})
            uid = attributes.get('idPessoa') or attributes.get('login')
        
        logger.info(f"UFSC OAuth - UID extraído: {uid}")
        return str(uid) if uid else None
    
    def extract_common_fields(self, data):
        """Mapear campos do OAuth UFSC para usuário Django"""
        logger.info("UFSC OAuth - Extraindo campos comuns")
        
        # Dados estão em 'attributes' conforme documentação da UFSC
        attributes = data.get('attributes', {})
        
        # Mapear campos conforme retorno da UFSC
        login = attributes.get('login', '')
        email = attributes.get('email', '')
        nome_social = attributes.get('nomeSocial', '')
        
        # Processar nome
        if nome_social:
            nomes = nome_social.split()
            first_name = nomes[0] if nomes else ''
            last_name = ' '.join(nomes[1:]) if len(nomes) > 1 else ''
        else:
            first_name = ''
            last_name = ''
        
        # Username: usar login, se for numérico usar primeiro nome
        username = login
        if login and login.isdigit() and first_name:
            username = first_name.lower()
        
        result = {
            'username': username,
            'email': email,
            'first_name': first_name,
            'last_name': last_name,
            'url': 'https://idufsc.ufsc.br/',  # ✅ ADICIONADO: URL do ID UFSC
        }
        
        logger.info(f"UFSC OAuth - Campos mapeados: {result}")
        return result
    
    def extract_email_addresses(self, data):
        """Extrair endereços de email verificados"""
        attributes = data.get('attributes', {})
        email = attributes.get('email')
        
        if email:
            return [CachedEmailAddress(
                email=email, 
                verified=True, 
                primary=True
            )]
        return []


# ✅ CORREÇÃO CRÍTICA: Registro manual compatível com Django 1.11/allauth
provider_registry = providers.registry
if hasattr(provider_registry, '_registry'):
    # Django 1.11 / allauth antigo
    provider_registry._registry['ufsc'] = UfscProvider
else:
    # Versão mais nova
    providers.registry.register(UfscProvider)
