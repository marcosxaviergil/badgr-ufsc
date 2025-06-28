# apps/badgrsocialauth/adapter.py

import logging
import urllib.request, urllib.parse, urllib.error

from allauth.account.utils import user_email
from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings
from django.http import HttpResponseForbidden, HttpResponseRedirect
from django.shortcuts import reverse
from rest_framework.exceptions import AuthenticationFailed

from badgeuser.authcode import accesstoken_for_authcode
from badgrsocialauth.utils import set_session_verification_email, get_session_authcode, generate_provider_identifier
from badgeuser.models import UserRecipientIdentifier, CachedEmailAddress  # ✅ ADICIONADO: CachedEmailAddress
from mainsite.models import BadgrApp

logger = logging.getLogger(__name__)


class BadgrSocialAccountAdapter(DefaultSocialAccountAdapter):

    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        logger.info(
            'social login authentication error: %s' % {
                'error': error,
                'exception': exception,
                'extra_context': extra_context,
            })
        badgr_app = BadgrApp.objects.get_current(request)
        redirect_url = "{url}?authError={message}".format(
            url=badgr_app.ui_login_redirect,
            message=urllib.parse.quote("Authentication error"))
        raise ImmediateHttpResponse(HttpResponseRedirect(redirect_to=redirect_url))

    def _update_session(self, request, sociallogin):
        email = user_email(sociallogin.user)
        set_session_verification_email(request, email)

    # ✅ MÉTODO CRÍTICO: Resolver "Sign Up Closed"
    def is_open_for_signup(self, request, sociallogin=None):
        """
        Para OAuth UFSC, sempre permitir signup mesmo se OPEN_FOR_SIGNUP=False
        """
        if sociallogin and sociallogin.account.provider == 'ufsc':
            return True  # Sempre permitir para UFSC
        
        # Para outros casos, usar configuração padrão
        return getattr(settings, 'OPEN_FOR_SIGNUP', True)

    # ✅ ADICIONADO: Método para pular formulário de signup para UFSC
    def is_auto_signup_allowed(self, request, sociallogin):
        """
        Para UFSC, sempre permitir auto signup (cadastro automático)
        """
        if sociallogin.account.provider == 'ufsc':
            return True
        return super().is_auto_signup_allowed(request, sociallogin)

    # ✅ CORRIGIDO: Método para completar dados automaticamente
    def populate_user(self, request, sociallogin, data):
        """
        Para UFSC, popular dados do usuário automaticamente
        """
        user = super().populate_user(request, sociallogin, data)
        
        if sociallogin.account.provider == 'ufsc':
            # Extrair dados da resposta da UFSC
            extra_data = sociallogin.account.extra_data
            attributes = extra_data.get('attributes', {})
            
            # ✅ CORREÇÃO: Mapeamento robusto de nome
            nome_completo = (
                attributes.get('nomeSocial') or
                attributes.get('nome') or
                attributes.get('personName') or
                'Usuario UFSC'
            ).strip()

            nome_parts = nome_completo.split(' ') if nome_completo else []
            
            # ✅ Garantir valores não nulos
            user.first_name = nome_parts[0] if nome_parts else 'Usuario'
            user.last_name = ' '.join(nome_parts[1:]) if len(nome_parts) > 1 else 'UFSC'
            
            # ✅ Email com fallback robusto
            user.email = attributes.get('email') or 'usuario@ufsc.br'
            
            # ✅ Username baseado no login
            username = attributes.get('login') or user.email.split('@')[0] or 'usuario_ufsc'
            user.username = username.lower().replace(' ', '_').replace('.', '_')
            
            # ✅ CORREÇÃO: Garantir que nenhum campo seja None ou vazio
            if not user.first_name or user.first_name.lower() in ['none', 'null', '']:
                user.first_name = 'Usuario'
            if not user.last_name or user.last_name.lower() in ['none', 'null', '']:
                user.last_name = 'UFSC'
            if not user.email or user.email.lower() in ['none', 'null', '']:
                user.email = 'usuario@ufsc.br'
        
        return user

    def save_user(self, request, sociallogin, form=None):
        """
        ✅ CORREÇÃO CRÍTICA: Cadastro transparente + verificação automática de email para UFSC
        Store verification email in session so that it can be retrieved/forwarded when redirecting to front-end.
        """
        self._update_session(request, sociallogin)

        # ✅ ADICIONADO: Para UFSC, criar usuário automaticamente
        if sociallogin.account.provider == 'ufsc':
            # Preencher dados automaticamente com informações da UFSC
            user = sociallogin.user
            
            # ✅ CORREÇÃO: Extrair dados da resposta OAuth antes de usar fallbacks
            extra_data = sociallogin.account.extra_data
            attributes = extra_data.get('attributes', {})
            
            # ✅ CORREÇÃO: Mapear nome completo primeiro
            nome_completo = (
                attributes.get('nomeSocial') or
                attributes.get('nome') or
                attributes.get('personName') or
                ''
            ).strip()
            
            if nome_completo:
                nome_parts = nome_completo.split(' ')
                user.first_name = nome_parts[0] if nome_parts else 'Usuario'
                user.last_name = ' '.join(nome_parts[1:]) if len(nome_parts) > 1 else 'UFSC'
            else:
                user.first_name = 'Usuario'
                user.last_name = 'UFSC'
            
            # ✅ CORREÇÃO: Email com fallback robusto
            user.email = attributes.get('email') or 'usuario@ufsc.br'
            
            # ✅ CORREÇÃO: Username baseado no login
            username = attributes.get('login') or user.email.split('@')[0] or 'usuario_ufsc'
            user.username = username.lower().replace(' ', '_').replace('.', '_')
            
            # ✅ CORREÇÃO: Garantir que nenhum campo seja None ou vazio
            if not user.first_name or user.first_name.lower() in ['none', 'null', '']:
                user.first_name = 'Usuario'
            if not user.last_name or user.last_name.lower() in ['none', 'null', '']:
                user.last_name = 'UFSC'
            if not user.email or user.email.lower() in ['none', 'null', '']:
                user.email = 'usuario@ufsc.br'
                
            # Definir senha automática (não será usada porque login é via OAuth)
            user.set_unusable_password()

        # Salvar usuário primeiro
        user = super(BadgrSocialAccountAdapter, self).save_user(request, sociallogin, form)

        # ✅ CORREÇÃO CRÍTICA: Verificar email automaticamente para UFSC
        if sociallogin.account.provider == 'ufsc':
            try:
                # Tentar encontrar o endereço de email
                email_address = CachedEmailAddress.cached.get(
                    user=user, 
                    email=user.email
                )
                
                # Forçar verificação se não estiver verificado
                if not email_address.verified:
                    email_address.verified = True
                    email_address.save()
                    logger.info(f"✅ Email {user.email} automaticamente verificado para usuário OAuth UFSC {user.username}")
                else:
                    logger.info(f"✅ Email {user.email} já estava verificado para usuário OAuth UFSC {user.username}")
                
            except CachedEmailAddress.DoesNotExist:
                # Criar email verificado se não existir
                email_address = CachedEmailAddress.objects.create(
                    user=user,
                    email=user.email,
                    verified=True,  # ✅ CRIAR JÁ VERIFICADO
                    primary=True
                )
                logger.info(f"✅ Email {user.email} criado como verificado para usuário OAuth UFSC {user.username}")
                
            except Exception as e:
                logger.error(f"❌ Erro ao verificar email para usuário UFSC {user.username}: {e}")

        # Para outros providers que precisam de identificador verificado
        if sociallogin.account.provider in getattr(settings, 'SOCIALACCOUNT_RECIPIENT_ID_PROVIDERS', ['twitter']):
            UserRecipientIdentifier.objects.create(user=user, verified=True, identifier=generate_provider_identifier(sociallogin))

        return user

    def get_connect_redirect_url(self, request, socialaccount):
        """
        Returns the default URL to redirect to after successfully
        connecting a social account. We hijack this process to see if a UserRecipientIdentifier needs to be added.
        """
        assert request.user.is_authenticated

        if socialaccount.provider in getattr(settings, 'SOCIALACCOUNT_RECIPIENT_ID_PROVIDERS', ['twitter']):
            UserRecipientIdentifier.objects.get_or_create(
                user=socialaccount.user, identifier=generate_provider_identifier(socialaccount=socialaccount),
                defaults={'verified': True}
            )

        url = reverse('socialaccount_connections')
        return url

    def pre_social_login(self, request, sociallogin):
        """
        ✅ CORREÇÃO CRÍTICA: Verificar email para usuários EXISTENTES também
        Retrieve and verify (again) auth token that was provided with initial connect request. Store as request.user,
        as required for socialauth connect logic.
        """
        self._update_session(request, sociallogin)
        
        # ✅ ADICIONADO: Para usuários UFSC existentes, verificar email automaticamente
        if sociallogin.account.provider == 'ufsc' and sociallogin.is_existing:
            try:
                existing_user = sociallogin.user
                email_address = CachedEmailAddress.cached.get(
                    user=existing_user, 
                    email=existing_user.email
                )
                
                if not email_address.verified:
                    email_address.verified = True
                    email_address.save()
                    logger.info(f"✅ Email {existing_user.email} verificado para usuário EXISTENTE OAuth UFSC {existing_user.username}")
                    
            except CachedEmailAddress.DoesNotExist:
                logger.warning(f"⚠️ Email não encontrado para usuário existente UFSC {existing_user.username}")
            except Exception as e:
                logger.error(f"❌ Erro ao verificar email para usuário existente UFSC: {e}")
        
        try:
            authcode = get_session_authcode(request)
            if authcode is not None:
                accesstoken = accesstoken_for_authcode(authcode)
                if not accesstoken:
                    raise ImmediateHttpResponse(HttpResponseForbidden())

                request.user = accesstoken.user
                if sociallogin.is_existing and accesstoken.user != sociallogin.user:
                    badgr_app = BadgrApp.objects.get_current(request)
                    redirect_url = "{url}?authError={message}".format(
                        url=badgr_app.ui_connect_success_redirect,
                        message=urllib.parse.quote("Could not add social login. This account is already associated with a user."))
                    raise ImmediateHttpResponse(HttpResponseRedirect(redirect_to=redirect_url))

        except AuthenticationFailed as e:
            raise ImmediateHttpResponse(HttpResponseForbidden(e.detail))
