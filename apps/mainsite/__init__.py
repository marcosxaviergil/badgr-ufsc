# apps/mainsite/__init__.py
# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import os
import sys

# Configurar UTF-8 se necessario
os.environ.setdefault('PYTHONIOENCODING', 'UTF-8')

# Build paths inside the project
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOP_DIR = os.path.dirname(BASE_DIR)

# Adiciona o diretorio de apps ao Python path
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

# Versao do Badgr
VERSION = (2, 0, 0, 'final', 0)

def get_version():
    """Return the version as a string."""
    version = '.'.join(str(x) for x in VERSION[:3])
    if VERSION[3] != 'final':
        version = '%s-%s%s' % (version, VERSION[3], VERSION[4])
    return version

__version__ = get_version()

# Importa do arquivo celery.py ao inves de celery_app.py
from .celery import app as celery_app

__all__ = ('celery_app',)
