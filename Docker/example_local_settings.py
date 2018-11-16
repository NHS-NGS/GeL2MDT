"""Local Settings for GeL2MDT"""

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '1321453215251231231'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False
ADMINS = [('Bioinformatics', 'email@center.nhs.uk'), ]
MANAGERS = ADMINS
# Allowed hosts
ALLOWED_HOSTS = ['*']

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'gel2mdt_db',
        'USER': 'paddy',
        'PASSWORD': '',
        'HOST': 'db',
        'PORT': '3306',
    },
}
from celery.schedules import crontab

CELERY_BROKER_URL = 'redis://redis:6379'
CELERY_RESULT_BACKEND = 'redis://redis:6379'
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TASK_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Europe/London'
CELERY_BEAT_SCHEDULE = {
    'task-number-one': {
        'task': 'gel2mdt.tasks.update_cases',
        'schedule': crontab(minute=0, hour=0),
    },
    'task-number-two': {
        'task': 'gel2mdt.tasks.listupdate_email',
        'schedule': crontab(minute=0, hour=7),
    },
    'task-number-three': {
        'task': 'gel2mdt.tasks.case_alert_email',
        'schedule': crontab(minute=0, hour=7),
    },
    'task-number-four': {
        'task': 'gel2mdt.tasks.update_report_email',
        'schedule': crontab(day_of_week=0),
    },
}

EMAIL_HOST = ''
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''