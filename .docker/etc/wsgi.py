# .docker/etc/wsgi.py

import os
import sys

# Configurar encoding UTF-8 antes de qualquer import Django
os.environ.setdefault('LANG', 'en_US.UTF-8')
os.environ.setdefault('LC_ALL', 'en_US.UTF-8')
os.environ.setdefault('PYTHONIOENCODING', 'UTF-8')

# Configurar locale de forma compativel com versoes antigas
try:
    import locale
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
except:
    # Fallback silencioso se locale nao disponivel
    try:
        import locale
        locale.setlocale(locale.LC_ALL, 'C.UTF-8')
    except:
        pass

# Adiciona o diretorio de apps ao Python path
sys.path.insert(0, '/badgr_server/apps')

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "mainsite.settings_local")

application = get_wsgi_application()