#!/bin/bash

# This script only needs to be run once on first setting up the Gel2MDT database. Assuming a persistent db, any new containers will not require this to be run again

# Create your own superuser account:
DJANGO_SUPERUSER=admin
DJANGO_EMAIL=admin@nhs.net
DJANGO_PASSWORD=a_password

# Django creates the database schema
cd /root/gel2mdt/gelweb/
python manage.py migrate
python manage.py makemigrations gel2mdt
python manage.py migrate
python manage.py createinitialrevisions
echo "from django.contrib.auth.models import User; User.objects.create_superuser('$DJANGO_SUPERUSER', '$DJANGO_EMAIL', '$DJANGO_PASSWORD')" | python manage.py shell

