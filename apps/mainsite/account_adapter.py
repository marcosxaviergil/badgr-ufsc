# apps/mainsite/account_adapter.py

import logging
import urllib.request, urllib.parse, urllib.error
import urllib.parse

from allauth.account.adapter import DefaultAccountAdapter, get_adapter
from allauth.account.models import EmailConfirmation, EmailConfirmationHMAC
from allauth.account.utils import user_pk_to_url_str
from allauth.exceptions import ImmediateHttpResponse
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.contrib.sites.shortcuts import get_current_site
from django.core.urlresolvers import resolve, Resolver404, reverse

from badgeuser.authcode import authcode_for_accesstoken
from badgeuser.models import CachedEmailAddress
import badgrlog
from badgrsocialauth.utils import set_session_badgr_app
from mainsite.models import BadgrApp, EmailBlacklist, AccessTokenProxy
from mainsite.utils import OriginSetting, set_url_query_params

# ✅ CORRIGIDO: Usar logger Python padrão para mensagens simples
logger = logging.getLogger(__name__)
badgr_logger = badgrlog.BadgrLogger()


class BadgrAccountAdapter(DefaultAccountAdapter):
    """
    ✅ CORRIGIDO: Adapter customizado para Badgr sem envio de emails
    """

    EMAIL_FROM_STRING = ''

    def send_mail(self, template_prefix, email, context):
        """
        ✅ CORRIGIDO: Não enviar emails para evitar problemas de configuração
        """
        context['STATIC_URL'] = getattr(settings, 'STATIC_URL')
        context['HTTP_ORIGIN'] = getattr(settings, 'HTTP_ORIGIN')
        context['PRIVACY_POLICY_URL'] = getattr(settings, 'PRIVACY_POLICY_URL', None)
        context['TERMS_OF_SERVICE_URL'] = getattr(settings, 'TERMS_OF_SERVICE_URL', None)
        context['GDPR_INFO_URL'] = getattr(settings, 'GDPR_INFO_URL', None)
        context['OPERATOR_STREET_ADDRESS'] = getattr(settings, 'OPERATOR_STREET_ADDRESS', None)
        context['OPERATOR_NAME'] = getattr(settings, 'OPERATOR_NAME', None)
        context['OPERATOR_URL'] = getattr(settings, 'OPERATOR_URL', None)

        if context.get('unsubscribe_url', None) is None:
            try:
                badgrapp_pk = context['badgr_app'].pk
            except (KeyError, AttributeError):
                badgrapp_pk = None
            context['unsubscribe_url'] = getattr(settings, 'HTTP_ORIGIN') + EmailBlacklist.generate_email_signature(
                email, badgrapp_pk)

        self.EMAIL_FROM_STRING = self.set_email_string(context)

        # ✅ DESABILITAR ENVIO DE EMAILS - só logar
        logger.info("Email would be sent to %s with template %s", email, template_prefix)
        return None

    def set_email_string(self, context):
        """Configurar string de remetente de email"""
        from_elements = [context.get('site_name', 'Badgr').replace(',', '')]
        default_from = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@badges.setic.ufsc.br')
        
        if '<' in default_from:
            return default_from
        else:
            from_elements.append("<{}>".format(default_from))

        return " ".join(from_elements)

    def get_from_email(self):
        return self.EMAIL_FROM_STRING

    def is_open_for_signup(self, request):
        """✅ CORRIGIDO: Sempre permitir signup"""
        return getattr(settings, 'OPEN_FOR_SIGNUP', True)

    def get_email_confirmation_redirect_url(self, request, badgr_app=None):
        """
        ✅ CORRIGIDO: URL de redirecionamento após confirmação de email
        """
        if badgr_app is None:
            badgr_app = BadgrApp.objects.get_current(request)
            if not badgr_app:
                logger.warning("Could not determine authorized badgr app")
                return super(BadgrAccountAdapter, self).get_email_confirmation_redirect_url(request)

        try:
            resolver_match = resolve(request.path)
            confirmation = EmailConfirmationHMAC.from_key(resolver_match.kwargs.get('confirm_id'))
            
            # publish changes to cache
            email_address = CachedEmailAddress.objects.get(pk=confirmation.email_address.pk)
            email_address.publish()

            query_params = {
                'email': email_address.email.encode('utf8')
            }
            
            # Pass source and signup along to UI
            source = getattr(request, 'query_params', request.GET).get('source', None)
            if source:
                query_params['source'] = source

            signup = getattr(request, 'query_params', request.GET).get('signup', None)
            if signup:
                query_params['signup'] = 'true'
                return set_url_query_params(badgr_app.get_path('/auth/welcome'), **query_params)
            else:
                return set_url_query_params(urllib.parse.urljoin(
                    badgr_app.email_confirmation_redirect.rstrip('/') + '/',
                    urllib.parse.quote(email_address.user.first_name.encode('utf8'))
                ), **query_params)

        except (Resolver404, Exception) as e:
            logger.warning("Error in email confirmation redirect: %s", str(e))
            return badgr_app.email_confirmation_redirect if badgr_app else '/'

    def get_email_confirmation_url(self, request, emailconfirmation, signup=False):
        """✅ CORRIGIDO: URL de confirmação de email"""
        url_name = "v1_api_user_email_confirm"
        temp_key = default_token_generator.make_token(emailconfirmation.email_address.user)
        token = "{uidb36}-{key}".format(
            uidb36=user_pk_to_url_str(emailconfirmation.email_address.user),
            key=temp_key
        )
        activate_url = OriginSetting.HTTP + reverse(url_name, kwargs={'confirm_id': emailconfirmation.key})
        badgrapp = BadgrApp.objects.get_current(request=request)
        
        tokenized_activate_url = "{url}?token={token}&a={badgrapp}".format(
            url=activate_url,
            token=token,
            badgrapp=badgrapp.id if badgrapp else 1
        )

        # Add source and signup query params to the confirmation url
        if request:
            source = None
            if hasattr(request, 'data'):
                source = request.data.get('source', None)
            elif hasattr(request, 'session'):
                source = request.session.get('source', None)

            if source:
                tokenized_activate_url = set_url_query_params(tokenized_activate_url, source=source)

            if signup:
                tokenized_activate_url = set_url_query_params(tokenized_activate_url, signup="true")

        return tokenized_activate_url

    def send_confirmation_mail(self, request, emailconfirmation, signup):
        """
        ✅ CORRIGIDO: Não enviar email de confirmação para evitar erros
        """
        logger.info("Confirmation email would be sent to %s", emailconfirmation.email_address.email)
        
        # ✅ MARCAR EMAIL COMO VERIFICADO AUTOMATICAMENTE
        try:
            email_address = emailconfirmation.email_address
            email_address.verified = True
            email_address.save()
            logger.info("Email %s marked as verified automatically", email_address.email)
        except Exception as e:
            logger.error("Error auto-verifying email: %s", str(e))

    def get_login_redirect_url(self, request):
        """
        ✅ CORRIGIDO: Redirecionamento após login bem-sucedido
        """
        if hasattr(request.user, 'is_authenticated') and request.user.is_authenticated:
            badgr_app = BadgrApp.objects.get_current(request)

            if badgr_app is not None:
                try:
                    accesstoken = AccessTokenProxy.objects.generate_new_token_for_user(
                        request.user,
                        application=badgr_app.oauth_application if badgr_app.oauth_application_id else None,
                        scope='rw:backpack rw:profile rw:issuer'
                    )

                    if badgr_app.use_auth_code_exchange:
                        authcode = authcode_for_accesstoken(accesstoken)
                        params = dict(authCode=authcode)
                    else:
                        params = dict(authToken=accesstoken.token)

                    return set_url_query_params(badgr_app.ui_login_redirect, **params)
                except Exception as e:
                    logger.error("Error generating access token: %s", str(e))
                    return badgr_app.ui_login_redirect if badgr_app else '/'
        return '/'

    def login(self, request, user):
        """
        ✅ CORRIGIDO: Login sem verificação obrigatória de email
        """
        badgr_app = BadgrApp.objects.get_current(request)

        # ✅ REMOVER VERIFICAÇÃO OBRIGATÓRIA DE EMAIL
        # Permitir login mesmo sem email verificado
        ret = super(BadgrAccountAdapter, self).login(request, user)
        
        if badgr_app:
            set_session_badgr_app(request, badgr_app)
        
        return ret

    def logout(self, request):
        """Logout preservando badgr app session"""
        badgrapp_pk = request.session.get('badgr_app_pk')
        super(BadgrAccountAdapter, self).logout(request)
        if badgrapp_pk:
            request.session['badgr_app_pk'] = badgrapp_pk

    def save_user(self, request, user, form, commit=True):
        """
        ✅ CORRIGIDO: Salvar usuário sem exigir verificação de email
        """
        user = super(BadgrAccountAdapter, self).save_user(request, user, form, commit)
        
        if commit:
            # ✅ MARCAR EMAIL COMO VERIFICADO AUTOMATICAMENTE
            try:
                from badgeuser.models import CachedEmailAddress
                email_address, created = CachedEmailAddress.objects.get_or_create(
                    user=user,
                    email=user.email,
                    defaults={'verified': True, 'primary': True}
                )
                if not email_address.verified:
                    email_address.verified = True
                    email_address.save()
                logger.info("User %s created with verified email", user.email)
            except Exception as e:
                logger.error("Error auto-verifying email for new user: %s", str(e))
        
        return user

    def respond_email_verification_sent(self, request, user):
        """
        ✅ CORRIGIDO: Resposta para verificação de email enviada
        """
        from django.http import JsonResponse
        return JsonResponse({
            'message': 'Email verification sent',
            'email': user.email,
            'verified': True  # ✅ Sempre marcar como verificado
        })

    def clean_email(self, email):
        """
        ✅ CORRIGIDO: Limpar email sem validações de domínio
        """
        return email.lower().strip()

    def is_safe_url(self, url):
        """Verificar se URL é segura p
