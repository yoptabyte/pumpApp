import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pampApp.settings')

app = Celery('pampApp')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
