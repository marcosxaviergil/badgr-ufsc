# apps/mainsite/views.py

import base64
import time

from django import forms
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
# from django.core.urlresolvers import reverse_lazy <--- comentado em favor da linha de baixo
from django.core.urlresolvers import reverse_lazy
from django.db import IntegrityError
from django.http import (HttpResponse, HttpResponseServerError,
                        HttpResponseNotFound, HttpResponseRedirect, JsonResponse)
from django.shortcuts import redirect
from django.template import loader, TemplateDoesNotExist
from django.utils.decorators import method_decorator
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import FormView, RedirectView
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.permissions import AllowAny
from rest_framework.renderers import JSONRenderer
from rest_framework.response import Response
from rest_framework.views import APIView

from issuer.tasks import rebake_all_assertions, update_issuedon_all_assertions
from mainsite.admin_actions import clear_cache
from mainsite.models import EmailBlacklist, BadgrApp
from mainsite.serializers import VerifiedAuthTokenSerializer
from pathway.tasks import resave_all_elements
import badgrlog

logger = badgrlog.BadgrLogger()

##
#
#  Error Handler Views
#
##
@xframe_options_exempt
def error404(request):
   try:
       template = loader.get_template('error/404.html')
   except TemplateDoesNotExist:
       return HttpResponseServerError('<h1>Page not found (404)</h1>', content_type='text/html')
   return HttpResponseNotFound(template.render({
       'STATIC_URL': getattr(settings, 'STATIC_URL', '/static/'),
   }))


@xframe_options_exempt
def error500(request):
   try:
       template = loader.get_template('error/500.html')
   except TemplateDoesNotExist:
       return HttpResponseServerError('<h1>Server Error (500)</h1>', content_type='text/html')
   return HttpResponseServerError(template.render({
       'STATIC_URL': getattr(settings, 'STATIC_URL', '/static/'),
   }))


def info_view(request):
   return redirect(getattr(settings, 'LOGIN_REDIRECT_URL'))


def email_unsubscribe_response(request, message, error=False):
   badgr_app_pk = request.GET.get('a', None)

   badgr_app = BadgrApp.objects.get_by_id_or_default(badgr_app_pk)

   query_param = 'infoMessage' if error else 'authError'
   redirect_url = "{url}?{query_param}={message}".format(
       url=badgr_app.ui_login_redirect,
       query_param=query_param,
       message=message)
   return HttpResponseRedirect(redirect_to=redirect_url)


def email_unsubscribe(request, *args, **kwargs):
   if time.time() > int(kwargs['expiration']):
       return email_unsubscribe_response(
           request, 'Your unsubscription link has expired.', error=True)

   try:
       email = base64.b64decode(kwargs['email_encoded'])
   except TypeError:
       logger.event(badgrlog.BlacklistUnsubscribeInvalidLinkEvent(kwargs['email_encoded']))
       return email_unsubscribe_response(request, 'Invalid unsubscribe link.',
                                         error=True)

   if not EmailBlacklist.verify_email_signature(**kwargs):
       logger.event(badgrlog.BlacklistUnsubscribeInvalidLinkEvent(email))
       return email_unsubscribe_response(request, 'Invalid unsubscribe link.',
                                         error=True)

   blacklist_instance = EmailBlacklist(email=email)
   try:
       blacklist_instance.save()
       logger.event(badgrlog.BlacklistUnsubscribeRequestSuccessEvent(email))
   except IntegrityError:
       pass
   except:
       logger.event(badgrlog.BlacklistUnsubscribeRequestFailedEvent(email))
       return email_unsubscribe_response(
           request, "Failed to unsubscribe email.",
           error=True)

   return email_unsubscribe_response(
       request, "You will no longer receive email notifications for earned"
       " badges from this domain.")


class AppleAppSiteAssociation(APIView):
   renderer_classes = (JSONRenderer,)
   permission_classes = (AllowAny,)

   def get(self, request):
       data = {
           "applinks": {
               "apps": [],
               "details": []
           }
       }

       for app_id in getattr(settings, 'APPLE_APP_IDS', []):
           data['applinks']['details'].append(app_id)

       return Response(data=data)


class LoginAndObtainAuthToken(ObtainAuthToken):
   serializer_class = VerifiedAuthTokenSerializer


class SitewideActionForm(forms.Form):
   ACTION_CLEAR_CACHE = 'CLEAR_CACHE'
   ACTION_RESAVE_ELEMENTS = 'RESAVE_ELEMENTS'
   ACTION_REBAKE_ALL_ASSERTIONS = "REBAKE_ALL_ASSERTIONS"
   ACTION_FIX_ISSUEDON = 'FIX_ISSUEDON'

   ACTIONS = {
       ACTION_CLEAR_CACHE: clear_cache,
       ACTION_RESAVE_ELEMENTS: resave_all_elements,
       ACTION_REBAKE_ALL_ASSERTIONS: rebake_all_assertions,
       ACTION_FIX_ISSUEDON: update_issuedon_all_assertions,
   }
   CHOICES = (
       (ACTION_CLEAR_CACHE, 'Clear Cache',),
       (ACTION_RESAVE_ELEMENTS, 'Re-save Pathway Elements',),
       (ACTION_REBAKE_ALL_ASSERTIONS, 'Rebake all assertions',),
       (ACTION_FIX_ISSUEDON, 'Re-process issuedOn for backpack assertions',),
   )

   action = forms.ChoiceField(choices=CHOICES, required=True, label="Pick an action")
   confirmed = forms.BooleanField(required=True, label='Are you sure you want to perform this action?')


class SitewideActionFormView(FormView):
   form_class = SitewideActionForm
   template_name = 'admin/sitewide_actions.html'
   success_url = reverse_lazy('admin:index')

   @method_decorator(staff_member_required)
   def dispatch(self, request, *args, **kwargs):
       return super(SitewideActionFormView, self).dispatch(request, *args, **kwargs)

   def form_valid(self, form):
       action = form.ACTIONS[form.cleaned_data['action']]

       if hasattr(action, 'delay'):
           action.delay()
       else:
           action()

       return super(SitewideActionFormView, self).form_valid(form)


class RedirectToUiLogin(RedirectView):
   def get_redirect_url(self, *args, **kwargs):
       badgrapp = BadgrApp.objects.get_current()
       return badgrapp.ui_login_redirect if badgrapp.ui_login_redirect is not None else badgrapp.email_confirmation_redirect


class DocsAuthorizeRedirect(RedirectView):
   def get_redirect_url(self, *args, **kwargs):
       badgrapp = BadgrApp.objects.get_current(request=self.request)
       url = badgrapp.oauth_authorization_redirect
       if not url:
           url = 'https://{cors}/auth/oauth2/authorize'.format(cors=badgrapp.cors)

       query = self.request.META.get('QUERY_STRING', '')
       if query:
           url = "{}?{}".format(url, query)
       return url


@csrf_exempt
def login_redirect(request):
   """Redireciona login do frontend para OAuth ou mantém login normal"""
   
   # Se tem provider específico nos parâmetros, redirecionar para OAuth
   provider = request.GET.get('provider')
   if provider:
       if provider == 'ufsc':
           return HttpResponseRedirect('/accounts/ufsc/login/')
       # Adicionar outros providers futuramente
   
   # Se é requisição AJAX/API, retornar JSON
   if request.headers.get('Content-Type') == 'application/json' or request.headers.get('Accept', '').startswith('application/json'):
       return JsonResponse({
           'loginUrl': 'https://api-badges.setic.ufsc.br/accounts/ufsc/login/',
           'providers': ['ufsc'],
           'message': 'Use OAuth providers for authentication'
       })
   
   # Para browsers normais, redirecionar para frontend
   return HttpResponseRedirect('https://badges.setic.ufsc.br/auth/login')


from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.contrib.auth import authenticate
from oauth2_provider.models import Application, AccessToken
import json

@api_view(['POST'])
@permission_classes([AllowAny])
def token_login(request):
   """Endpoint para login que retorna token OAuth2 diretamente"""
   username = request.data.get('username')
   password = request.data.get('password')
   
   # Autenticar usuário
   user = authenticate(username=username, password=password)
   if not user:
       return Response({'error': 'Invalid credentials'}, status=400)
   
   # Buscar application "public"
   try:
       application = Application.objects.get(client_id='public')
   except Application.DoesNotExist:
       return Response({'error': 'OAuth2 not configured'}, status=500)
   
   # Limpar tokens antigos do usuário (opcional)
   AccessToken.objects.filter(user=user, application=application).delete()
   
   # Criar token (versão corrigida para django-oauth-toolkit 1.1.2)
   import uuid
   from datetime import datetime, timedelta
   from django.utils import timezone
   
   token = AccessToken.objects.create(
       user=user,
       application=application,
       token=uuid.uuid4().hex,  # ✅ CORRIGIDO: Gerar token manualmente
       expires=timezone.now() + timedelta(seconds=86400),  # 24 horas
       scope='rw:profile rw:issuer rw:backpack'
   )
   
   return Response({
       'access_token': token.token,
       'token_type': 'Bearer',
       'expires_in': 86400,
       'scope': token.scope,
       'user': {
           'id': user.id,
           'email': user.email,
           'first_name': user.first_name,
           'last_name': user.last_name,
       }
   })
