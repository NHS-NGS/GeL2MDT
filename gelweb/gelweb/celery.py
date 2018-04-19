import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gelweb.settings.charlie_db')

app = Celery('gel2mdt')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()