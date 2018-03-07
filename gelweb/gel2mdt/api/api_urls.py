from django.contrib import admin
from django.urls import path
from . import api_views

api_urlpatterns = [
    path('api/rare-disease', api_views.rare_disease_json, name='rare-disease-json'),
]
