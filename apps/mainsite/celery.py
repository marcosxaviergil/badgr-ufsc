# apps/mainsite/celery.py

from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# Caminho correto do módulo de configuração do Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mainsite.settings_local')

app = Celery('mainsite')

# Carrega configurações do Django com namespace 'CELERY'
app.config_from_object('django.conf:settings', namespace='CELERY')

# Autodiscover de tasks nos apps registrados
app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
