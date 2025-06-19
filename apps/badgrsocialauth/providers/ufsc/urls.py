# apps/badgrsocialauth/providers/ufsc/urls.py

from allauth.socialaccount.providers.oauth2.urls import default_urlpatterns
from .provider import UfscProvider

urlpatterns = default_urlpatterns(UfscProvider)
