# apps/badgrsocialauth/views.py

import urllib.request, urllib.parse, urllib.error
import urllib.parse

from allauth.account.adapter import get_adapter
from allauth.socialaccount.providers.base import AuthProcess
from django.contrib.auth import logout
from django.core.exceptions import ValidationError
from django.urls import reverse, NoReverseMatch
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.views.generic import RedirectView
from django.shortcuts import redirect
from django.views.decorators.csrf import csrf_exempt
from rest_framework.exceptions import AuthenticationFailed
import requests
import base64

from badgeuser.authcode import authcode_for_accesstoken
from badgeuser.models import CachedEmailAddress, BadgeUser
from badgrsocialauth.models import Saml2Account, Saml2Configuration
from badgrsocialauth.utils import (set_session_badgr_app, get_session_badgr_app,
                                   get_session_verification_email, set_session_authcode,)
from django.conf import settings
from mainsite.models import BadgrApp
from mainsite.utils import set_url_query_params

from saml2 import BINDING_HTTP_POST, entity
from saml2.client import Saml2Client
from saml2.config import Config as Saml2Config
from mainsite.models import AccessTokenProxy


class BadgrSocialLogin(RedirectView):
    def get(self, request, *args, **kwargs):
        try:
            logout(request)
            return super(BadgrSocialLogin, self).get(request, *args, **kwargs)
        except ValidationError as e:
            return HttpResponseBadRequest(e.message)
        except AuthenticationFailed as e:
            return HttpResponseForbidden(e.detail)

    def get_redirect_url(self):
        provider_name = self.request.GET.get('provider', None)
        if provider_name is None:
            raise ValidationError('No provider specified')

        badgr_app = BadgrApp.objects.get_current(request=self.request)
        if badgr_app is not None:
            set_session_badgr_app(self.request, badgr_app)
        else:
            raise ValidationError('Unable to save BadgrApp in session')

        self.request.session['source'] = self.request.GET.get('source', None)

        try:
            if 'saml2' in provider_name:
                redirect_url = reverse('saml2login', args=[provider_name])
            else:
                redirect_url = reverse('{}_login'.format(provider_name))
        except (NoReverseMatch, TypeError):
            raise ValidationError('No {} provider found'.format(provider_name))

        authcode = self.request.GET.get('authCode', None)
        if authcode is not None:
            set_session_authcode(self.request, authcode)
            return set_url_query_params(redirect_url, process=AuthProcess.CONNECT)
        else:
            return redirect_url


class BadgrSocialLoginCancel(RedirectView):
    def get_redirect_url(self):
        badgr_app = BadgrApp.objects.get_current(self.request)
        if badgr_app is not None:
            return set_url_query_params(badgr_app.ui_login_redirect)


class BadgrSocialEmailExists(RedirectView):
    def get_redirect_url(self):
        badgr_app = BadgrApp.objects.get_current(self.request)
        if badgr_app is not None:
            verification_email = self.request.session.get('verification_email', '')
            provider = self.request.session.get('socialaccount_sociallogin', {}).get('account', {}).get('provider', '')
            return set_url_query_params(
                badgr_app.ui_signup_failure_redirect,
                authError='An account already exists with provided email address',
                email=base64.urlsafe_b64encode(verification_email.encode('utf-8')),
                socialAuthSlug=provider
            )


class BadgrSocialAccountVerifyEmail(RedirectView):
    def get_redirect_url(self):
        badgr_app = BadgrApp.objects.get_current(self.request)
        verification_email = get_session_verification_email(self.request)

        if verification_email is not None:
            verification_email = urllib.parse.quote(verification_email.encode('utf-8'))
        else:
            verification_email = ''

        if badgr_app is not None:
            base_64_email = base64.urlsafe_b64encode(verification_email.encode('utf-8'))
            return urllib.parse.urljoin(badgr_app.ui_signup_success_redirect.rstrip('/') + '/', base_64_email.decode())


class BadgrAccountConnected(RedirectView):
    def get_redirect_url(self):
        badgr_app = BadgrApp.objects.get_current(self.request)
        if badgr_app is not None:
            return set_url_query_params(badgr_app.ui_connect_success_redirect)


def saml2_client_for(idp_name=None):
    config = Saml2Configuration.objects.get(slug=idp_name)
    metadata = config.cached_metadata if config else None

    if not metadata:
        r = requests.get(config.metadata_conf_url)
        metadata = r.text

    origin = getattr(settings, 'HTTP_ORIGIN').split('://')[1]
    https_acs_url = 'https://' + origin + reverse('assertion_consumer_service', args=[idp_name])

    setting = {
        'metadata': {'inline': [metadata]},
        'entityid': "badgrserver",
        'service': {
            'sp': {
                'endpoints': {'assertion_consumer_service': [(https_acs_url, BINDING_HTTP_POST)]},
                'allow_unsolicited': True,
                'authn_requests_signed': False,
                'logout_requests_signed': True,
                'want_assertions_signed': True,
                'want_response_signed': False,
            },
        },
    }
    spConfig = Saml2Config()
    spConfig.load(setting)
    spConfig.allow_unknown_attributes = True
    return Saml2Client(config=spConfig), config


@csrf_exempt
def assertion_consumer_service(request, idp_name):
    saml_client, config = saml2_client_for(idp_name)
    authn_response = saml_client.parse_authn_request_response(request.POST.get('SAMLResponse'), entity.BINDING_HTTP_POST)
    authn_response.get_identity()

    if not any(key in authn_response.ava for key in settings.SAML_EMAIL_KEYS):
        raise ValidationError(f'Missing email in SAML assertions: {list(authn_response.ava.keys())}')

    if not any(key in authn_response.ava for key in settings.SAML_FIRST_NAME_KEYS):
        raise ValidationError(f'Missing first_name in SAML assertions: {list(authn_response.ava.keys())}')

    if not any(key in authn_response.ava for key in settings.SAML_LAST_NAME_KEYS):
        raise ValidationError(f'Missing last_name in SAML assertions: {list(authn_response.ava.keys())}')

    email = [authn_response.ava[key][0] for key in settings.SAML_EMAIL_KEYS if key in authn_response.ava][0]
    first_name = [authn_response.ava[key][0] for key in settings.SAML_FIRST_NAME_KEYS if key in authn_response.ava][0]
    last_name = [authn_response.ava[key][0] for key in settings.SAML_LAST_NAME_KEYS if key in authn_response.ava][0]
    badgr_app = BadgrApp.objects.get(pk=request.session.get('badgr_app_pk'))
    return auto_provision(request, email, first_name, last_name, badgr_app, config, idp_name)


def auto_provision(request, email, first_name, last_name, badgr_app, config, idp_name):
    def login(user):
        accesstoken = AccessTokenProxy.objects.generate_new_token_for_user(user, scope='rw:backpack rw:profile rw:issuer')
        if badgr_app.use_auth_code_exchange:
            return redirect(set_url_query_params(badgr_app.ui_login_redirect, authCode=authcode_for_accesstoken(accesstoken)))
        return redirect(set_url_query_params(badgr_app.ui_login_redirect, authToken=accesstoken.token))

    def new_account():
        new_user = BadgeUser.objects.create(email=email, first_name=first_name, last_name=last_name, request=request, send_confirmation=False)
        cached_email = CachedEmailAddress.objects.get(email=email)
        cached_email.verified = True
        cached_email.save()
        Saml2Account.objects.create(config=config, user=new_user, uuid=email)
        return new_user

    saml2_account = Saml2Account.objects.filter(uuid=email).first()
    if saml2_account:
        return login(saml2_account.user)

    try:
        existing_email = CachedEmailAddress.cached.get(email=email)
        if not existing_email.verified:
            return login(new_account())
        Saml2Account.objects.create(config=config, user=existing_email.user, uuid=email)
        return redirect(set_url_query_params(badgr_app.ui_signup_failure_redirect, authError='An account already exists with provided email address', email=base64.urlsafe_b64encode(email.encode()).decode(), socialAuthSlug=idp_name))
    except CachedEmailAddress.DoesNotExist:
        return login(new_account())


def saml2_redirect(request, idp_name):
    saml_client, _ = saml2_client_for(idp_name)
    _, info = saml_client.prepare_for_authenticate()
    redirect_url = next((v for k, v in info['headers'] if k == 'Location'), None)
    response = redirect(redirect_url)
    response['Cache-Control'] = 'no-cache, no-store'
    response['Pragma'] = 'no-cache'
    badgr_app = BadgrApp.objects.get_current(request)
    request.session['badgr_app_pk'] = badgr_app.pk
    return response
