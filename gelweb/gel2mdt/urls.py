from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('rare-disease-main', views.rare_disease_main, name='rare-disease-main'),
    path('cancer-main', views.cancer_main, name='cancer-main'),

    path('proband/<int:gel_id>', views.proband_view, name='proband-view'),
    path('update_proband/<int:gel_id>', views.update_proband, name='update-proband'),

    path('start_mdt/', views.start_mdt_view, name='start-mdt'),
    path('edit_mdt/<int:mdt_id>', views.edit_mdt, name='edit-mdt'),
    path('mdt_view/<int:mdt_id>', views.mdt_view, name='mdt-view'),

    path('add_ir_to_mdt/<int:mdt_id>/<int:irreport_id>', views.add_ir_to_mdt, name='add-ir-to-mdt'),
    path('remove_ir_from_mdt/<int:mdt_id>/<int:irreport_id>', views.remove_ir_from_mdt, name='remove-ir-from-mdt'),

    path('edit_mdt_variant/<int:pv_id>', views.edit_mdt_variant, name='edit-mdt-variant'),
    path('edit_mdt_proband/<int:proband_id>', views.edit_mdt_proband, name='edit-mdt-proband'),
]