#!/bin/bash

# This script only needs to be run once on first setting up the Gel2MDT database. Assuming a persistent db, any new containers will not require this to be run again

# Create your own superuser account:
DJANGO_SUPERUSER=user
DJANGO_EMAIL=user@center.nhs.uk
DJANGO_PASSWORD=admin_password

# Django creates the database schema
. /root/gel2mdt/Docker/startup_script.sh
cd /root/gel2mdt/gelweb/
python manage.py migrate
python manage.py makemigrations gel2mdt
python manage.py migrate
python manage.py createinitialrevisions
python manage.py collectstatic --noinput
echo "from django.contrib.auth.models import User; User.objects.create_superuser('$DJANGO_SUPERUSER', '$DJANGO_EMAIL', '$DJANGO_PASSWORD')" | python manage.py shell
