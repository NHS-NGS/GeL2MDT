from django.contrib import admin
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

from .api.api_urls import *

urlpatterns = [
    path('', views.rare_disease_main, name='rare-disease-main'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('profile/remove_case/<int:case_id>', views.remove_case, name='remove-case'),
    path('rare-disease-main', views.rare_disease_main, name='rare-disease-main'),

    path('proband/<int:report_id>', views.proband_view, name='proband-view'),
    path('pull_t3_variants/<int:report_id>', views.pull_t3_variants, name='pull-t3-variants'),
    path('proband/<int:report_id>/negative_report', views.negative_report, name='negative_report'),
    path('update_proband/<int:report_id>', views.update_proband, name='update-proband'),
    path('variant_for_validation/<int:pv_id>', views.variant_for_validation, name='variant-for-validation'),
    path('validation_list', views.validation_list, name='validation-list'),

    path('variant/<int:variant_id>', views.variant_view, name='variant-view'),

    path('panel/<int:panelversion_id>', views.panel_view, name='panel'),

    path('select_transcript/<int:report_id>/<int:pv_id>', views.select_transcript, name='select-transcript'),
    path('update_transcript/<int:report_id>/<int:pv_id>/<int:transcript_id>', views.update_transcript,
         name='update-transcript'),

    path('start_mdt/', views.start_mdt_view, name='start-mdt'),
    path('edit_mdt/<int:mdt_id>', views.edit_mdt, name='edit-mdt'),
    path('mdt_view/<int:mdt_id>', views.mdt_view, name='mdt-view'),
    path('mdt_proband_view/<int:mdt_id>/<int:pk>/<int:important>', views.mdt_proband_view, name='mdt-proband-view'),

    path('add_ir_to_mdt/<int:mdt_id>/<int:irreport_id>', views.add_ir_to_mdt, name='add-ir-to-mdt'),
    path('remove_ir_from_mdt/<int:mdt_id>/<int:irreport_id>', views.remove_ir_from_mdt, name='remove-ir-from-mdt'),

    path('edit_mdt_proband/<int:report_id>', views.edit_mdt_proband, name='edit-mdt-proband'),

    path('recent_mdts/', views.recent_mdts, name='recent-mdt'),
    path('add_variant/<int:report_id>', views.add_variant, name='add-variant'),

    path('delete_mdt/<int:mdt_id>', views.delete_mdt, name='delete-mdt'),
    path('export_mdt/<int:mdt_id>', views.export_mdt, name='export-mdt'),
    path('export_mdt_outcome_form/<int:report_id>', views.export_mdt_outcome_form, name='export-mdt-outcome'),

    path('select_attendees_for_mdt/<int:mdt_id>', views.select_attendees_for_mdt, name='select-attendees-for-mdt'),
    path('add_attendee_to_mdt/<int:mdt_id>/<int:attendee_id>/<str:role>', views.add_attendee_to_mdt,
         name='add-attendee-to-mdt'),
    path('remove_attendee_from_mdt/<int:mdt_id>/<int:attendee_id>/<str:role>', views.remove_attendee_from_mdt,
         name='remove-attendee-from-mdt'),
    path('add_new_attendee/', views.add_new_attendee, name='add-new-attendee'),

    path(r'genomics_england_report/<int:report_id>', views.genomics_england_report, name='genomics-england-report'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_DIR)

urlpatterns += api_urlpatterns
