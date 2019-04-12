"""Copyright (c) 2018 Great Ormond Street Hospital for Children NHS Foundation
Trust & Birmingham Women's and Children's NHS Foundation Trust

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from django.contrib import admin
from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic.base import RedirectView
from .api.api_urls import *

urlpatterns = [
    path('', views.index, name='index'),
    path('user_admin/', views.user_admin, name='user_admin'),
    path('delete_group/<int:id>', views.delete_group, name='delete_group'),
    path('edit_group/<int:id>', views.edit_group, name='edit_group'),
    path('edit_user/<int:id>', views.edit_user, name='edit_user'),
    path('register/', views.register, name='register'),
    path('profile/', views.profile, name='profile'),
    path('profile/remove_case/<int:case_id>', views.remove_case, name='remove-case'),
    path('cancer-main', views.cancer_main, name='cancer-main'),
    path('rare-disease-main', views.rare_disease_main, name='rare-disease-main'),
    path('proband/<int:report_id>', views.proband_view, name='proband-view'),
    path('edit_relative/<int:relative_id>', views.edit_relatives, name='edit-relatives'),
    path('pull_t3_variants/<int:report_id>', views.pull_t3_variants, name='pull-t3-variants'),
    path('proband/<int:report_id>/report/<str:outcome>', views.report, name='report'),
    path('update_proband/<int:report_id>', views.update_proband, name='update-proband'),
    path('update_demographics/<int:report_id>', views.update_demographics, name='update-demographics'),
    path('ajax_validation', views.ajax_variant_validation, name='ajax_validation'),
    path('<str:sample_type>/validation_list', views.validation_list, name='validation-list'),

    path('variant/<int:variant_id>', views.variant_view, name='variant-view'),
    path('sv/<int:variant_id>', views.sv_view, name='sv-view'),
    path('str/<int:variant_id>', views.str_view, name='str-view'),

    path('panel/<int:panelversion_id>', views.panel_view, name='panel'),

    path('select_transcript/<int:report_id>/<int:pv_id>', views.select_transcript, name='select-transcript'),
    path('update_transcript/<int:report_id>/<int:pv_id>/<int:transcript_id>', views.update_transcript,
         name='update-transcript'),
    path('edit_preferred_transcript/<int:geneid>/<int:genome_build_id>', views.edit_preferred_transcript,
         name='edit-preferred-transcript'),
    path('update_preferred_transcript/<int:geneid>/<int:genome_build_id>/<int:transcript_id>',
         views.update_preferred_transcript, name='update-preferred-transcript'),
    path('<str:sample_type>/start_mdt/', views.start_mdt_view, name='start-mdt'),
    path('<str:sample_type>/edit_mdt/<int:mdt_id>', views.edit_mdt, name='edit-mdt'),
    path('mdt_view/<int:mdt_id>', views.mdt_view, name='mdt-view'),
    path('mdt_proband_view/<int:mdt_id>/<int:pk>/<int:important>', views.mdt_proband_view, name='mdt-proband-view'),
    path('mdt_cnv_view/<int:mdt_id>/<int:pk>/', views.mdt_cnv_view, name='mdt-cnv-view'),
    path('mdt_str_view/<int:mdt_id>/<int:pk>/', views.mdt_str_view, name='mdt-str-view'),

    path('add_ir_to_mdt/<int:mdt_id>/<int:irreport_id>', views.add_ir_to_mdt, name='add-ir-to-mdt'),
    path('remove_ir_from_mdt/<int:mdt_id>/<int:irreport_id>', views.remove_ir_from_mdt, name='remove-ir-from-mdt'),

    path('edit_mdt_proband/<int:report_id>', views.edit_mdt_proband, name='edit-mdt-proband'),

    path('<str:sample_type>/recent_mdts/', views.recent_mdts, name='recent-mdt'),

    path('delete_mdt/<int:mdt_id>', views.delete_mdt, name='delete-mdt'),
    path('export_mdt/<int:mdt_id>', views.export_mdt, name='export-mdt'),
    path('export_mdt_outcome_form/<int:report_id>', views.export_mdt_outcome_form, name='export-mdt-outcome'),
    path('export_gtab_template/<int:report_id>', views.export_gtab_template, name='export-gtab-template'),

    path('select_attendees_for_mdt/<int:mdt_id>', views.select_attendees_for_mdt, name='select-attendees-for-mdt'),
    path('add_attendee_to_mdt/<int:mdt_id>/<int:attendee_id>/<str:role>', views.add_attendee_to_mdt,
         name='add-attendee-to-mdt'),
    path('remove_attendee_from_mdt/<int:mdt_id>/<int:attendee_id>/<str:role>', views.remove_attendee_from_mdt,
         name='remove-attendee-from-mdt'),
    path('add_new_attendee/', views.add_new_attendee, name='add-new-attendee'),

    path(r'genomics_england_report/<int:report_id>', views.genomics_england_report, name='genomics-england-report'),
    path('<str:sample_type>/audit/', views.audit, name='audit'),
    path('<str:sample_type>/gene_search/', views.search_by_gene, name='gene_search'),
    path('<str:sample_type>/case_alert/', views.case_alert, name='case-alert'),
    path('edit_case_alert/<int:case_alert_id>', views.edit_case_alert, name='edit-case-alert'),
    path('add_case_alert/', views.add_case_alert, name='add-case-alert'),
    path('delete_comment/<int:comment_id>', views.delete_comment, name='delete-comment'),
    path('edit_comment/<int:comment_id>', views.edit_comment, name='edit-comment'),
    path('delete_case_alert/<int:case_alert_id>', views.delete_case_alert, name='delete-case-alert'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_DIR)

urlpatterns += api_urlpatterns
