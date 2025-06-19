# wsgi.py

import os
import sys

# Configurar encoding UTF-8 antes de qualquer import Django
os.environ.setdefault('LANG', 'C.UTF-8')
os.environ.setdefault('LC_ALL', 'C.UTF-8')
os.environ.setdefault('PYTHONIOENCODING', 'UTF-8')

# Configurar locale de forma compatível com versões antigas
try:
    import locale
    locale.setlocale(locale.LC_ALL, 'C.UTF-8')
except:
    # Fallback silencioso se locale não disponível
    try:
        import locale
        locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
    except:
        pass

# Adiciona o diretório de apps ao Python path (compatível com Docker)
sys.path.insert(0, '/badgr_server/apps')

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mainsite.settings_local")

application = get_wsgi_application()
