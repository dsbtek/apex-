import os
from celery import Celery
from decouple import config
# test cicd in celery
environment = config('ENVIRONMENT')
os.environ.setdefault('DJANGO_SETTINGS_MODULE',
                      'atg_web.settings.'+environment)

app = Celery('atg_web')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()
