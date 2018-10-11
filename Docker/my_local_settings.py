"""Local Settings for GeL2MDT"""

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'PickYourOwnSecurityKeyHere'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allowed hosts
ALLOWED_HOSTS = ['localhost',
                 '127.0.0.1']

# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'gel2mdt_db',
        'USER': 'gel2mdtuser',
        'PASSWORD': 'gel2mdtpassword',  # Need to set env var
        'HOST': 'db',  # IP of the dbserver
        'PORT': '5432',
    },
}
