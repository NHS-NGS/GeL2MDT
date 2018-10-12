"""Local Settings for GeL2MDT"""

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'PickYourOwnSecurityKeyHere'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allowed hosts
ALLOWED_HOSTS = ['*']

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'gel2mdt_db',
        'USER': 'gel2mdtuser',
        'PASSWORD': 'gel2mdtpassword',
        'HOST': 'db',
        'PORT': '5432',
    },
}
