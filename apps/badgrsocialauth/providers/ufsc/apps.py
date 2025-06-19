# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class UfscProviderConfig(AppConfig):
    name = 'badgrsocialauth.providers.ufsc'
    label = 'badgrsocialauth_providers_ufsc'
    verbose_name = _('Badgr Social Auth UFSC Provider')
    
    # Remover o método ready() daqui - o registro será feito pelo app principal