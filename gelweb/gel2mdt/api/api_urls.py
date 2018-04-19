from django.contrib import admin
from django.urls import path
from . import api_views

api_urlpatterns = [
    path(
        'api/gelir/<str:sample_type>',
        api_views.RareDiseaseCases.as_view(),
        name='gelir-json'
    ),
]
