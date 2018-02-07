from django.contrib import admin
from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('register/', views.register, name='register'),
    path('rare-disease-main', views.rare_disease_main, name='rare-disease-main'),
    path('cancer-main', views.cancer_main, name='cancer-main'),

    path('main_cases/', views.main_cases, name='main-cases'),
    path('pilot_cases/', views.pilot_cases, name='pilot-cases'),

    path('proband/<int:report_id>', views.proband_view, name='proband-view'),
    path('update_proband/<int:report_id>', views.update_proband, name='update-proband'),

    path('start_mdt/', views.start_mdt_view, name='start-mdt'),
    path('edit_mdt/<int:mdt_id>', views.edit_mdt, name='edit-mdt'),
    path('mdt_view/<int:mdt_id>', views.mdt_view, name='mdt-view'),

    path('add_ir_to_mdt/<int:mdt_id>/<int:irreport_id>', views.add_ir_to_mdt, name='add-ir-to-mdt'),
    path('remove_ir_from_mdt/<int:mdt_id>/<int:irreport_id>', views.remove_ir_from_mdt, name='remove-ir-from-mdt'),

    path('edit_mdt_variant/<int:pv_id>', views.edit_mdt_variant, name='edit-mdt-variant'),
    path('edit_mdt_proband/<int:proband_id>', views.edit_mdt_proband, name='edit-mdt-proband'),

    path('recent_mdts/', views.recent_mdts, name='recent-mdt'),

    path('delete_mdt/<int:mdt_id>', views.delete_mdt, name='delete-mdt'),

    path('select_attendees_for_mdt/<int:mdt_id>', views.select_attendees_for_mdt, name='select-attendees-for-mdt'),
    path('add_attendee_to_mdt/<int:mdt_id>/<int:attendee_id>/<str:role>', views.add_attendee_to_mdt,
         name='add-attendee-to-mdt'),
    path('remove_attendee_from_mdt/<int:mdt_id>/<int:attendee_id>/<str:role>', views.remove_attendee_from_mdt,
         name='remove-attendee-from-mdt'),
    path('add_new_attendee/', views.add_new_attendee, name='add-new-attendee'),
]