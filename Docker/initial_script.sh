cd /root/gel2mdt/gelweb/
python manage.py migrate
python manage.py makemigrations gel2mdt
python manage.py migrate
python manage.py createinitialrevisions
echo "from django.contrib.auth.models import User; User.objects.create_superuser('DJANGO_SUPERUSER', 'DJANGO_EMAIL', 'DJANGO_PASSWORD')" | python manage.py shell

