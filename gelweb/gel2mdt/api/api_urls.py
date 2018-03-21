from django.contrib import admin
from django.urls import path
from . import api_views

api_urlpatterns = [
    path(
        'api/rare-disease',
        api_views.RareDiseaseCases.as_view(),
        name='rare-disease-json'
    ),
    path(
        'api/proband_variants/<int:pk>',
        api_views.ProbandVariants.as_view(),
        name='proband-variants'
    ),
    path(
        'api/proband/<int:pk>',
        api_views.ProbandDetail.as_view(),
        name='proband-json'
    ),
]
