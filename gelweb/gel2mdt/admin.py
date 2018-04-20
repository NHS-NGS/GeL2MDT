from django.contrib import admin
from django.apps import apps
from reversion import revisions
from gel2mdt.models import *


app = apps.get_app_config('gel2mdt')
for model_name, model in app.models.items():
    admin.site.register(model)
    revisions.register(model)

