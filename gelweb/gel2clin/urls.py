from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('cancer-main', views.cancer_main, name='cancer-main'),
    path('rare-disease-main', views.rare_disease_main, name='rare-disease-main'),
    path('proband/<int:report_id>', views.proband_view, name='proband-view'),
]