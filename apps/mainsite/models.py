# apps/mainsite/models.py

import base64
import hashlib
import re
import urllib.parse
from collections import OrderedDict

from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.exceptions import ValidationError, ImproperlyConfigured
from django.core.files.storage import DefaultStorage
from django.db import models
from django.utils.deconstruct import deconstructible
from oauth2_provider.models import get_application_model

import cachemodel
from entity.models import BaseVersionedEntity

Application = get_application_model()


class EmailBlacklist(cachemodel.CacheModel):
    email = models.EmailField(unique=True)

    class Meta:
        verbose_name = 'Blacklisted email'
        verbose_name_plural = 'Blacklisted emails'

    @staticmethod
    def generate_email_signature(email):
        return hashlib.md5(email + settings.UNSUBSCRIBE_SECRET_KEY).hexdigest()

    @staticmethod
    def verify_email_signature(email_encoded, expiration, signature):
        email = base64.b64decode(email_encoded)
        expected_signature = EmailBlacklist.generate_email_signature(email)
        return expected_signature == signature


class BadgrAppManager(models.Manager):
    def get_current(self, request=None, raise_exception=True):
        """
        Get the current BadgrApp. In multitenant mode, this is determined by
        the HTTP_ORIGIN header. In single tenant mode, this is the default BadgrApp.
        It will always return a BadgrApp if
        the server is properly configured.
        :param request: Django Request object
        :param raise_exception: bool
        :return: BadgrApp
        """
        origin = None
        existing_session_app_id = None

        if request:
            if request.META.get('HTTP_ORIGIN'):
                origin = request.META.get('HTTP_ORIGIN')
            elif request.META.get('HTTP_REFERER'):
                origin = request.META.get('HTTP_REFERER')
            existing_session_app_id = request.session.get('badgr_app_pk', None)

        if existing_session_app_id:
            try:
                return self.get(id=existing_session_app_id)
            except self.model.DoesNotExist:
                pass

        if origin:
            url = urllib.parse.urlparse(origin)
            try:
                return self.get(cors=url.netloc)
            except self.model.DoesNotExist:
                pass
        if raise_exception:
            return self.get(is_default=True)
        else:
            return self.get_by_id_or_default()

    def get_by_id_or_default(self, badgrapp_id=None):
        if badgrapp_id:
            try:
                return self.get(id=badgrapp_id)
            except (self.model.DoesNotExist, ValueError,):
                pass
        try:
            return self.get(is_default=True)
        except (self.model.DoesNotExist, self.model.MultipleObjectsReturned,):
            badgrapp = None
            legacy_default_setting = getattr(settings, 'BADGR_APP_ID', None)
            if legacy_default_setting is not None:
                try:
                    badgrapp = self.get(id=legacy_default_setting)
                except self.model.DoesNotExist:
                    pass
            else:
                badgrapp = self.first()

            if badgrapp is not None:
                badgrapp.is_default = True
                badgrapp.save()
                return badgrapp

            # ✅ FAILSAFE CUSTOMIZADO: usar configurações do settings ao invés de localhost:81
            from django.conf import settings
            
            # Usar domínios das configurações ou fallback para valores mais sensatos
            default_cors = getattr(settings, 'DEFAULT_BADGR_CORS', 'badges.setic.ufsc.br')
            default_protocol = 'https' if getattr(settings, 'ACCOUNT_DEFAULT_HTTP_PROTOCOL', 'https') == 'https' else 'http'
            base_url = f"{default_protocol}://{default_cors}"
            
            return self.create(
                name='Badgr UFSC Default',
                cors=default_cors,
                is_default=True,
                signup_redirect=f'{base_url}/signup/',
                email_confirmation_redirect=f'{base_url}/auth/login/',
                forgot_password_redirect=f'{base_url}/change-password/',
                ui_login_redirect=f'{base_url}/auth/login/',
                ui_signup_success_redirect=f'{base_url}/recipient/',
                ui_signup_failure_redirect=f'{base_url}/auth/login/?error=signup_failed',
                ui_connect_success_redirect=f'{base_url}/profile/',
                public_pages_redirect=f'{base_url}/public/',
                oauth_authorization_redirect=f'{base_url}/auth/oauth2/authorize/'
            )
        except self.model.MultipleObjectsReturned:
            badgrapp = self.filter(is_default=True).first()
            badgrapp.save()  # trigger one-default-only setting
            return badgrapp


class BadgrApp(cachemodel.CacheModel):
    name = models.CharField(max_length=254)
    cors = models.CharField(max_length=254, unique=True)
    is_default = models.BooleanField(default=False)
    email_confirmation_redirect = models.URLField()
    signup_redirect = models.URLField()
    forgot_password_redirect = models.URLField()
    ui_login_redirect = models.URLField(null=True)
    ui_signup_success_redirect = models.URLField(null=True)
    ui_connect_success_redirect = models.URLField(null=True)
    ui_signup_failure_redirect = models.URLField(null=True)
    public_pages_redirect = models.URLField(null=True)
    oauth_authorization_redirect = models.URLField(null=True)
    use_auth_code_exchange = models.BooleanField(default=False)
    oauth_application = models.ForeignKey("oauth2_provider.Application", null=True, blank=True)

    objects = BadgrAppManager()

    PROPS_FOR_DEFAULT = [
        'forgot_password_redirect', 'ui_login_redirect', 'ui_signup_success_redirect', 'ui_connect_success_redirect',
        'ui_signup_failure_redirect', 'oauth_authorization_redirect', 'email_confirmation_redirect'
    ]

    def __str__(self):
        return self.cors

    def get_path(self, path='/', use_https=None):
        if use_https is None:
            use_https = self.signup_redirect.startswith('https')
        scheme = 'https://' if use_https else 'http://'
        return '{}{}{}'.format(scheme, self.cors, path)

    @property
    def oauth_application_client_id(self):
        if self.oauth_application is None:
            return None
        return self.oauth_application.client_id

    @oauth_application_client_id.setter
    def oauth_application_client_id(self, value):
        # Allows setting of OAuth Application foreign key by client_id. Raises Application.DoesNotExist when not found
        # This does not save the record, so .save() must be called as appropriate.
        if value is None:
            self.oauth_application = None
        else:
            self.oauth_application = Application.objects.get(client_id=value)

    def save(self, *args, **kwargs):
        if self.is_default:
            # Set all other BadgrApp instances as no longer the default.
            self.__class__.objects.filter(is_default=True).exclude(id=self.pk).update(is_default=False)
        else:
            if not self.__class__.objects.filter(is_default=True).exists():
                self.is_default = True

        for prop in self.PROPS_FOR_DEFAULT:
            if not getattr(self, prop):
                setattr(self, prop, self.signup_redirect)
        return super(BadgrApp, self).save(*args, **kwargs)


@deconstructible
class DefinedScopesValidator(object):
    message = "Does not match defined scopes"
    code = 'invalid'

    def __call__(self, value):
        defined_scopes = set(getattr(settings, 'OAUTH2_PROVIDER', {}).get('SCOPES', {}).keys())
        provided_scopes = set(s.strip() for s in re.split(r'[\s\n]+', value))
        if provided_scopes - defined_scopes:
            raise ValidationError(self.message, code=self.code)
        pass

    def __eq__(self, other):
        return isinstance(other, self.__class__)


class ApplicationInfo(cachemodel.CacheModel):
    application = models.OneToOneField('oauth2_provider.Application')
    icon = models.FileField(blank=True, null=True)
    name = models.CharField(max_length=254, blank=True, null=True, default=None)
    website_url = models.URLField(blank=True, null=True, default=None)
    allowed_scopes = models.TextField(blank=False, validators=[DefinedScopesValidator()])
    trust_email_verification = models.BooleanField(default=False)

    def get_visible_name(self):
        if self.name:
            return self.name
        return self.application.name

    def get_icon_url(self):
        if self.icon:
            return self.icon.url

    @property
    def scope_list(self):
        return [s for s in re.split(r'[\s\n]+', self.allowed_scopes) if s]


class AccessTokenProxyManager(models.Manager):

    def generate_new_token_for_user(self, user, scope='r:profile', application=None, expires=None, refresh_token=None):
        """
        Generate a new AccessToken for the given user. Deletes any existing tokens for this user with the same scope.
        """
        from oauth2_provider.models import AccessToken
        if application is None:
            try:
                application = Application.objects.get(client_id="public")
            except Application.DoesNotExist:
                raise ImproperlyConfigured("You must define an oauth2_provider Application with client_id 'public'")

        # delete other tokens for this user
        AccessToken.objects.filter(user=user, application=application, scope=scope).delete()

        # Generate a new token
        new_token = AccessToken.objects.create(
            user=user,
            application=application,
            scope=scope,
            expires=expires
        )
        return AccessTokenProxy.objects.get(pk=new_token.pk)


class AccessTokenProxy(models.Model):

    class Meta:
        proxy = True
        verbose_name = 'access token'

    objects = AccessTokenProxyManager()

    def __getattr__(self, name):
        from oauth2_provider.models import AccessToken
        return getattr(AccessToken.objects.get(pk=self.pk), name)

    def __setattr__(self, name, value):
        try:
            super(AccessTokenProxy, self).__setattr__(name, value)
        except AttributeError:
            from oauth2_provider.models import AccessToken
            setattr(AccessToken.objects.get(pk=self.pk), name, value)

    def save(self, *args, **kwargs):
        if not hasattr(self, 'pk') or self.pk is None:
            raise ValueError("Cannot save AccessTokenProxy without pk")
        from oauth2_provider.models import AccessToken
        return AccessToken.objects.get(pk=self.pk).save(*args, **kwargs)


class LegacyTokenProxyManager(models.Manager):
    def get_from_entity_id(self, entity_id):
        legacy_entity_id = "legacy:" + entity_id
        return self.get(entity_id=legacy_entity_id)


class LegacyTokenProxy(BaseVersionedEntity):

    class Meta:
        proxy = True
        verbose_name = 'legacy auth token'

    objects = LegacyTokenProxyManager()

    @property
    def obscured_token(self):
        if self.entity_id:
            return "{}***".format(self.entity_id[:4])

    @property
    def user(self):
        from rest_framework.authtoken.models import Token
        if self.entity_id.startswith("legacy:"):
            token_key = self.entity_id[7:]
            try:
                token = Token.objects.get(key=token_key)
                return token.user
            except Token.DoesNotExist:
                pass
        return None