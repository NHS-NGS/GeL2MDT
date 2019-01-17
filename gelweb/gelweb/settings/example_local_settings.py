"""Local Settings for GeL2MDT"""

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ''

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allowed hosts
ALLOWED_HOSTS = ['localhost',
                 '127.0.0.1']

# Any addtional installed Django apps for inclusion in settings (e.g. 'mod_wsgi.server')
ADDITIONAL_APPS = []

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': '',
        'NAME': 'gel2mdt_db',
        'USER': '',
        'PASSWORD': '',  # Need to set env var
        'HOST': '',  # IP of the dbserver
        'PORT': '',
        'CONN_MAX_AGE': 500,
        'OPTIONS': {
            'sql_mode': 'TRADITIONAL',
            'charset': 'utf8mb4',
        },
        'TEST': {
            'NAME': 'django_test_gel2mdt',
        },
    },
}
