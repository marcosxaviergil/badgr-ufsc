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
from badgeuser.models import UserRecipientIdentifier
from mainsite.models import BadgrApp


class BadgrSocialAccountAdapter(DefaultSocialAccountAdapter):

    def authentication_error(self, request, provider_id, error=None, exception=None, extra_context=None):
        logging.getLogger(__name__).info(
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

    def save_user(self, request, sociallogin, form=None):
        """
        Store verification email in session so that it can be retrieved/forwarded when redirecting to front-end.
        ✅ ADICIONADO: Auto-verificar email para provider UFSC
        """
        self._update_session(request, sociallogin)

        user = super(BadgrSocialAccountAdapter, self).save_user(request, sociallogin, form)

        # ✅ AUTO-VERIFICAR EMAIL PARA UFSC
        if sociallogin.account.provider == 'ufsc':
            user.email_verified = True
            user.save()
            
            # Marcar EmailAddress como verificado também
            from allauth.account.models import EmailAddress
            try:
                email_address = EmailAddress.objects.get(email=user.email, user=user)
                email_address.verified = True
                email_address.save()
            except EmailAddress.DoesNotExist:
                EmailAddress.objects.create(
                    user=user,
                    email=user.email,
                    verified=True,
                    primary=True
                )

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
        Retrieve and verify (again) auth token that was provided with initial connect request.  Store as request.user,
        as required for socialauth connect logic.
        ✅ ADICIONADO: Auto-verificar para UFSC antes do login
        """
        self._update_session(request, sociallogin)
        
        # ✅ AUTO-VERIFICAR UFSC ANTES DO LOGIN
        if sociallogin.account.provider == 'ufsc':
            # Marcar email addresses como verificados
            for email_address in sociallogin.email_addresses:
                email_address.verified = True
        
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

    def get_login_redirect_url(self, request):
        """
        ✅ CORREÇÃO CRÍTICA: Redirecionar corretamente após login UFSC
        """
        badgr_app = BadgrApp.objects.get_current(request)
        
        # Para login social UFSC bem-sucedido, redirecionar para o dashboard
        if hasattr(request, 'session') and 'socialaccount_state' in request.session:
            # Verificar se é UFSC
            provider = getattr(request.session.get('socialaccount_sociallogin', {}).get('account', {}), 'provider', None)
            if provider == 'ufsc':
                return badgr_app.ui_signup_success_redirect or 'https://badges.setic.ufsc.br/recipient'
        
        # Fallback para comportamento padrão
        return badgr_app.ui_login_redirect or 'https://badges.setic.ufsc.br/auth/login'

    def get_signup_redirect_url(self, request):
        """
        ✅ ADICIONADO: Redirecionar corretamente após signup UFSC
        """
        badgr_app = BadgrApp.objects.get_current(request)
        
        # Para signup social UFSC, redirecionar para success
        return badgr_app.ui_signup_success_redirect or 'https://badges.setic.ufsc.br/recipient'