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
import os
import json
import csv
from datetime import datetime
from io import BytesIO, StringIO

from django.db import IntegrityError
from django.db.models import Q, Count
from django.http import HttpResponseRedirect, HttpResponse, JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.contrib import messages
from django.contrib.auth.models import User, Group
from django.contrib.auth.decorators import login_required, user_passes_test
from django.forms import modelformset_factory

from easy_pdf.rendering import render_to_pdf_response

from .config import load_config
from .forms import *
from .models import *
from .filters import *
from .tasks import *
from .exports import write_mdt_outcome_template, write_mdt_export, write_gtab_template
from .decorators import user_is_clinician

from .api.api_views import *

from .database_utils.multiple_case_adder import MultipleCaseAdder
from .vep_utils.run_vep_batch import CaseVariant

from bokeh.resources import CDN
from bokeh.embed import components
from bokeh.layouts import gridplot, row


def register(request):
    '''
    Registers a new user and adds them to a role table
    :param request:
    :return: The user will then have to contact admin to authenticate them
    '''
    registered = False
    username = ''

    if request.method == 'POST':
        user_form = UserForm(data=request.POST)

        if user_form.is_valid():
            first_name = user_form.cleaned_data['first_name']
            last_name = user_form.cleaned_data['last_name']
            full_name = f'{first_name} {last_name}'
            if len(last_name) >= 6:
                username = (last_name[:5] + first_name[0]).lower()
            else:
                username = (last_name + first_name[0]).lower()
            password = user_form.cleaned_data['password']
            email = user_form.cleaned_data['email']
            role = user_form.cleaned_data['role']
            hospital = user_form.cleaned_data['hospital']
            try:
                user = User(username=username, first_name=first_name, last_name=last_name, password=password,
                            email=email, is_active=False)
                user.save()
                user.set_password(user.password)
                user.save()
                registered = True
                if role == 'Clinical Scientist':
                    cs, created = ClinicalScientist.objects.get_or_create(
                        email=email)
                    cs.name = full_name
                    cs.hospital = hospital
                    cs.save()

                elif role == 'Clinician':
                    clinician, created = Clinician.objects.get_or_create(
                        email=email)
                    clinician.name = full_name
                    clinician.hospital = hospital
                    clinician.added_by_user = True
                    clinician.save()

                elif role == 'Other Staff':
                    other, created = OtherStaff.objects.get_or_create(
                        email=email)
                    other.name = full_name
                    other.hospital = hospital
                    other.save()

            except IntegrityError:
                messages.error(request, 'If you have already registered, '
                                        'please contact Bioinformatics to activate your account')
                return HttpResponseRedirect('/register')

    else:
        user_form = UserForm()

    return render(request, 'registration/registration.html',
                  {'user_form': user_form, 'registered': registered, 'username': username})


@login_required
def profile(request):
    '''
    Profile page. Users can see their cases assigned to them and role info
    :param request:
    :return:
    '''
    role = None
    rolename = None

    cs = ClinicalScientist.objects.filter(email=request.user.email).first()
    other = OtherStaff.objects.filter(email=request.user.email).first()
    clinician = Clinician.objects.filter(email=request.user.email).first()

    my_cases = GELInterpretationReport.objects.latest_cases_by_user(
        username=request.user
    )

    if cs:
        rolename = 'Clinical Scientist'
        role = cs
    elif clinician:
        rolename = 'Clinician'
        role = clinician
    elif other:
        rolename = 'Other Staff'
        role = other
    if request.method == 'POST':
        form = ProfileForm(request.POST)
        if form.is_valid():
            if request.user.is_staff:
                if role:
                    role.delete() # Delete the old role
                    rolename = form.cleaned_data['role']
            if rolename == 'Clinical Scientist':
                cs, created = ClinicalScientist.objects.update_or_create(
                    name=request.user.first_name + ' ' + request.user.last_name,
                    email=request.user.email,
                    defaults={'hospital': form.cleaned_data['hospital']})
            elif rolename == 'Clinician':
                clinician, created = Clinician.objects.update_or_create(
                    name=request.user.first_name + ' ' + request.user.last_name,
                    email=request.user.email,
                    defaults={'hospital': form.cleaned_data['hospital'],
                              'added_by_user': True})
            elif rolename == 'Other Staff':
                other, created = OtherStaff.objects.update_or_create(
                    name=request.user.first_name + ' ' + request.user.last_name,
                    email=request.user.email,
                    defaults={'hospital':form.cleaned_data['hospital']})
            messages.add_message(request, 25, 'Profile Updated')
            return HttpResponseRedirect('/profile')
        else:
            print(form.errors)
    else:
        if role:
            form = ProfileForm(initial={'role': rolename, 'hospital': role.hospital})
        else:
            form = ProfileForm(initial={'role': 'Unknown', 'hospital': 'Unknown'})
    return render(request, 'gel2mdt/profile.html', {'form': form,
                                                    'role':role,
                                                    'my_cases': my_cases,
                                                    'rolename':rolename})


@login_required
def index(request):
    '''
    A choice between the raredisease and cancer portal

    :param request:
    :return:
    '''
    clinicians_emails = Clinician.objects.all().values_list('email', flat=True)
    if request.user.is_staff:
        return render(request, 'gel2mdt/index.html', {'sample_type': None})
    elif request.user.email not in clinicians_emails:
        return render(request, 'gel2mdt/index.html', {'sample_type': None})
    else:
        return redirect('gel2clin:index')


@login_required
def remove_case(request, case_id):
    '''
    Users can remove a case from their assigned cases

    :param request:
    :param case_id: Report id of case that they want to remove
    :return: Back to profile page
    '''
    case = GELInterpretationReport.objects.get(id=case_id)
    case.assigned_user = None
    case.save(overwrite=True)
    return redirect('profile')


@login_required
@user_is_clinician(url='cancer-main')
def cancer_main(request):
    '''
    Shows all the Cancer cases the user has access to and allows easy searching of cases

    :param request:
    :return:
    '''
    gene_search_form = GeneSearchForm()
    return render(request, 'gel2mdt/cancer_main.html', {'sample_type': 'cancer',
                                                        'gene_search_form': gene_search_form})


@login_required
@user_is_clinician(url='rare-disease-main')
def rare_disease_main(request):
    '''
    Shows all the RD cases the user has access to and allows easy searching of cases

    :param request:
    :return:
    '''
    gene_search_form = GeneSearchForm()
    return render(request, 'gel2mdt/rare_disease_main.html', {'sample_type': 'raredisease',
                                                              'gene_search_form': gene_search_form})


@login_required
def search_by_gene(request, sample_type):
    latest_reports = GELInterpretationReport.objects.latest_cases_by_sample_type(
        sample_type=sample_type
    )
    gene_search_form = GeneSearchForm()
    proband_variants = []
    gene = None
    if request.method == 'POST':
        gene_search_form = GeneSearchForm(request.POST)
        if gene_search_form.is_valid():
            gene = gene_search_form.cleaned_data['gene']
            genes = Gene.objects.filter(hgnc_name__icontains=gene_search_form.cleaned_data['gene'])
            proband_variants = ProbandVariant.objects.filter(probandtranscriptvariant__transcript__gene__in=genes,
                                                             interpretation_report__in=latest_reports).distinct()
    return render(request, 'gel2mdt/gene_search.html', {'gene_search_form': gene_search_form,
                                                        'proband_variants': proband_variants,
                                                        'gene': gene,
                                                        'sample_type': sample_type})



@login_required
@user_is_clinician(url='proband-view')
def proband_view(request, report_id):
    '''
    Shows details about a particular proband, some fields are editable by clinical scientists

    :param request:
    :param report_id: GEL Report ID
    :return:
    '''
    report = GELInterpretationReport.objects.get(id=report_id)
    report_history_formatter = ReportHistoryFormatter(report=report)
    report_history = report_history_formatter.get_report_history()
    proband_history = report_history_formatter.get_proband_history()
    other_cases = GELInterpretationReport.objects.latest_cases_by_sample_type(report.sample_type).filter(
        ir_family__participant_family=report.ir_family.participant_family).exclude(ir_family=report.ir_family)

    if request.method == "POST":
        demogs_form = DemogsForm(request.POST, instance=report.ir_family.participant_family.proband)
        case_assign_form = CaseAssignForm(request.POST, instance=report)
        panel_form = PanelForm(request.POST)
        clinician_form = ClinicianForm(request.POST)
        add_clinician_form = AddClinicianForm(request.POST)
        add_variant_form = AddVariantForm(request.POST)
        variant_validation_form = VariantValidationForm(request.POST)

        if variant_validation_form.is_valid():
            validation_status = variant_validation_form.cleaned_data['validation_status']
            validation_user = variant_validation_form.cleaned_data['validation_responsible_user']

            pv.validation_status = validation_status
            pv.validation_responsible_user = validation_user
            pv.save()

        if demogs_form.is_valid():
            demogs_form.save()
            messages.add_message(request, 25, 'Proband Updated')
        if case_assign_form.is_valid():
            case_assign_form.save()
        if panel_form.is_valid():
            irfp, created = InterpretationReportFamilyPanel.objects.get_or_create(panel=panel_form.cleaned_data['panel'],
                                                                                  ir_family=report.ir_family,
                                                                                  defaults={
                                                                                    'custom': True,
                                                                                   'average_coverage':None,
                                                                                   'proportion_above_15x':None,
                                                                                   'genes_failing_coverage':None})
            messages.add_message(request, 25, 'Panel Added')
        if clinician_form.is_valid():
            family = report.ir_family.participant_family
            family.clinician = clinician_form.cleaned_data['clinician']
            family.save()
            messages.add_message(request, 25, 'Clinician Changed')
        if add_clinician_form.is_valid():
            clinician, created = Clinician.objects.get_or_create(email=add_clinician_form.cleaned_data['email'],
                                                                 defaults={
                                                                     'name': add_clinician_form.cleaned_data['name'],
                                                                     'hospital':add_clinician_form.cleaned_data['hospital'],
                                                                     'added_by_user': True
                                                                 })
            messages.add_message(request, 25, 'Clinician Created')
        if add_variant_form.is_valid():
            variant = CaseVariant(add_variant_form.cleaned_data['chromosome'],
                                  add_variant_form.cleaned_data['position'],
                                  report_id,
                                  1,
                                  add_variant_form.cleaned_data['reference'],
                                  add_variant_form.cleaned_data['alternate'],
                                  str(report.assembly))
            variant_entry, created = Variant.objects.get_or_create(chromosome=add_variant_form.cleaned_data['chromosome'],
                                                                   position=add_variant_form.cleaned_data['position'],
                                                                   genome_assembly=report.assembly,
                                                                   reference=add_variant_form.cleaned_data['reference'],
                                                                   alternate=add_variant_form.cleaned_data['alternate'],
                                                                   defaults={'db_snp_id': add_variant_form.cleaned_data['db_snp_id']})
            VariantAdder(variant_entry=variant_entry,
                         report=report,
                         variant=variant)
            messages.add_message(request, 25, 'Variant Added to Report')

    relatives = Relative.objects.filter(proband=report.ir_family.participant_family.proband)
    proband_form = ProbandForm(instance=report.ir_family.participant_family.proband)
    gelir_form = GELIRForm(instance=report)
    demogs_form = DemogsForm(instance=report.ir_family.participant_family.proband)
    proband_variants = ProbandVariant.objects.filter(interpretation_report=report)
    proband_mdt = MDTReport.objects.filter(interpretation_report=report)
    panels = InterpretationReportFamilyPanel.objects.filter(ir_family=report.ir_family)
    panel_form = PanelForm()
    case_assign_form = CaseAssignForm(instance=report)
    clinician_form = ClinicianForm()
    add_clinician_form = AddClinicianForm()
    add_variant_form = AddVariantForm()

    variants_for_reporting = RareDiseaseReport.objects.filter(
        proband_variant__interpretation_report__id=report.id,
        classification__in=('3','4','5'),
        proband_variant__validation_status="P"
    )

    pv_forms_dict = {}
    for pv in proband_variants:
        pv_forms_dict[pv] = VariantValidationForm(instance=pv)

    if not request.user.is_staff:
        if report.case_status == "C":
            for field in proband_form.__dict__["fields"]:
                proband_form.fields[field].widget.attrs['readonly'] = True
                proband_form.fields[field].widget.attrs['disabled'] = True

    return render(request, 'gel2mdt/proband.html', {'report': report,
                                                    'relatives': relatives,
                                                    'proband_form': proband_form,
                                                    'demogs_form': demogs_form,
                                                    'case_assign_form': case_assign_form,
                                                    'pv_forms_dict': pv_forms_dict,
                                                    'proband_mdt': proband_mdt,
                                                    'panels': panels,
                                                    'panel_form': panel_form,
                                                    'clinician_form':clinician_form,
                                                    'add_clinician_form':add_clinician_form,
                                                    'sample_type': report.sample_type,
                                                    'add_variant_form': add_variant_form,
                                                    'variants_for_reporting': variants_for_reporting,
                                                    'gelir_form': gelir_form,
                                                    'report_history': report_history,
                                                    'proband_history': proband_history,
                                                    'report_fields': report_history_formatter.report_interesting_fields,
                                                    'proband_fields': report_history_formatter.proband_interesting_fields,
                                                    'other_cases': other_cases})


@login_required
@user_is_clinician(url='index')
def edit_relatives(request, relative_id):
    """
    Allows users to edit relative demographic information

    :param request:
    :param relative_id: Relative ID
    :return:
    """
    data = {}
    relative = Relative.objects.get(id=relative_id)
    relative_form = RelativeForm(instance=relative)
    if request.method == 'POST':
        relative_form = RelativeForm(request.POST, instance=relative)
        if relative_form.is_valid():
            relative_form.save()
            data['form_is_valid'] = True
    context = {'relative_form': relative_form, 'relative': relative}
    html_form = render_to_string('gel2mdt/modals/relative_form.html', context, request=request)
    data['html_form'] = html_form
    return JsonResponse(data)


@login_required
@user_is_clinician(url='proband-view')
def update_demographics(request, report_id):
    '''
    Allows staff users to redo labkey lookup
    :param request:
    :param report_id: Report to redo lookup for
    :return: Back to proband page
    '''
    update_demo = UpdateDemographics(report_id=report_id)
    update_demo.update_clinician()
    update_demo.update_demographics()
    return HttpResponseRedirect(f'/proband/{report_id}')


def ajax_variant_validation(request):
    """
    Accepts a POST request to change the validation status of a particular
    ProbandVariant, the ID of which should be supplied in the JSON.
    """
    proband_variant_id = request.POST.get('probandVariant')
    selected_validation_status = request.POST.get('selectedStatus')
    selected_validation_user = request.POST.get('selectedUser')
    if selected_validation_user == "---------":
        user_instance = None
    else:
        user_instance = User.objects.get(username=selected_validation_user)

    validation_status_key = {
        'Unknown': 'U',
        'Awaiting Validation':'A',
        'Urgent Validation': 'K',
        'In Progress': 'I',
        'Passed Validation':'P',
        'Failed Validation': 'F',
        'Not Required': 'N',
    }
    selected_validation_status = validation_status_key[selected_validation_status]

    proband_variant = ProbandVariant.objects.get(id=proband_variant_id)

    proband_variant.validation_status = selected_validation_status
    proband_variant.validation_responsible_user = user_instance

    if not proband_variant.validation_datetime_set:
        proband_variant.validation_datetime_set = timezone.now()

    proband_variant.save()
    proband_variant = ProbandVariant.objects.get(id=proband_variant_id)

    new_validation_status = proband_variant.validation_status
    new_validation_user = proband_variant.validation_responsible_user
    if new_validation_user:
        new_validation_user = new_validation_user.username
    else:
        new_validation_user = None


    response = json.dumps({
        "success": True,
        "validationStatus": new_validation_status,
        "validationUser": new_validation_user
    })

    return HttpResponse(response, content_type="application/json")


@login_required
def validation_list(request, sample_type):
    '''
    Returns the list of proband variants that require validation
    :param request:
    :param sample_type: Either raredisease or cancer
    :return: View containing proband variants
    '''

    proband_variants = ProbandVariant.objects.filter(
        Q(validation_status="A") | Q(validation_status="K") | Q(validation_status="I"),
        interpretation_report__sample_type=sample_type)
    pv_forms_dict = {proband_variant: VariantValidationForm(instance=proband_variant)
                     for proband_variant in proband_variants}
    return render(request, 'gel2mdt/validation_list.html', {'pv_forms_dict': pv_forms_dict,
                                                            'sample_type': sample_type})


@login_required
@user_is_clinician(url='proband-view')
def pull_t3_variants(request, report_id):
    '''
    Allows users to download T3 variants for a case
    :param request:
    :param report_id: GEL Interpretationreport id
    :return: Back to proband page
    '''
    update_for_t3.delay(report_id)
    messages.add_message(request, 25, 'Please reload this page in a few minutes to see your Tier 3 Variants')
    return HttpResponseRedirect(f'/proband/{report_id}')


def panel_view(request, panelversion_id):
    '''
    Replicates panelapp but specifc for panel Version
    :param request:
    :param panelversion_id: PanelVersion ID
    :return: Panel View details
    '''
    panel = PanelVersion.objects.get(id=panelversion_id)
    config_dict = load_config.LoadConfig().load()
    panelapp_file = f'{config_dict["panelapp_storage"]}/{panel.panel.panelapp_id}_{panel.version_number}.json'
    if os.path.isfile(panelapp_file):
        panelapp_json = json.load(open(panelapp_file))
        return render(request, 'gel2mdt/panel.html', {'panel':panel,
                                                      'genes': panelapp_json['result']['Genes']})


@login_required
def variant_view(request, variant_id):
    '''
    Shows details about a particular variant and also probands it is present in
    :param request:
    :param variant_id: Variant ID
    :return:
    '''
    variant = Variant.objects.get(id=variant_id)
    try:
        transcript_variant = TranscriptVariant.objects.filter(variant=variant_id)[:1].get() #gets one (for hgvs_g)
    except TranscriptVariant.DoesNotExist:
        transcript_variant = None
    proband_variants = ProbandVariant.objects.filter(variant=variant)

    return render(request, 'gel2mdt/variant.html', {'variant': variant,
                                                    'transcript_variant': transcript_variant,
                                                    'proband_variants': proband_variants})


@login_required
@user_is_clinician(url='proband-view')
def update_proband(request, report_id):
    '''
    Updates the Proband page for fields used by clinical scientists such as status and outcomes
    :param request:
    :param report_id: GEL Report ID
    :return: Proband view
    '''
    report = GELInterpretationReport.objects.get(id=report_id)
    if request.method == "POST":
        proband_form = ProbandForm(request.POST, instance=report.ir_family.participant_family.proband)
        gelir_form = GELIRForm(request.POST, instance=report)
        if proband_form.is_valid() and gelir_form.is_valid():
            proband_form.save()
            gelir_form.save()
            messages.add_message(request, 25, 'Proband Updated')
        else:
            print(proband_form.errors)
        return HttpResponseRedirect(f'/proband/{report_id}')


@login_required
@user_is_clinician(url='proband-view')
def select_transcript(request, report_id, pv_id):
    '''
    Shows the transcript table and allows a user to select preferred transcript
    :param request:
    :param report_id: GEL Interpretationreport id
    :param pv_id: ProbandVariant id
    :return: View containing list of transcripts
    '''
    proband_transcript_variants = ProbandTranscriptVariant.objects.filter(proband_variant__id=pv_id)
    # Just selecting first selected transcript
    selected_count = 0
    for ptv in proband_transcript_variants:
        if ptv.selected:
            if selected_count == 0:
                pass
            else:
                ptv.selected = False
                ptv.save()
            selected_count += 1
    report = GELInterpretationReport.objects.get(id=report_id)
    return render(request, 'gel2mdt/select_transcript.html',
                  {'proband_transcript_variants': proband_transcript_variants,
                   'report': report})


@login_required
@user_is_clinician(url='proband-view')
def update_transcript(request, report_id, pv_id, transcript_id):
    '''
    Updates the selected transcript
    :param request:
    :param report_id: GEL Interpretationreport id
    :param pv_id: ProbandVariant id
    :param transcript_id: Transcript id of the selected transcript
    :return: Select Transcript view
    '''
    transcript = Transcript.objects.get(id=transcript_id)
    proband_variant = ProbandVariant.objects.get(id=pv_id)
    proband_variant.select_transcript(selected_transcript=transcript)
    messages.add_message(request, 25, 'Transcript Updated')
    return HttpResponseRedirect(f'/select_transcript/{report_id}/{proband_variant.id}')


@login_required
def start_mdt_view(request, sample_type):
    '''
    Creates a new MDT instance
    :param request:
    :param sample_type: Either raredisease or Cancer MDT will be created
    :return: View allowing users choose cases
    '''
    mdt_instance = MDT(creator=request.user, date_of_mdt=datetime.now(), sample_type=sample_type)
    mdt_instance.save()

    return HttpResponseRedirect(f'/{sample_type}/edit_mdt/{mdt_instance.id}')


@login_required
def edit_mdt(request, sample_type, mdt_id):
    '''
    Allows users to select which cases they want to bring to MDT
    :param request:
    :param sample_type: Either raredisease or cancer and will filter which cases appear in list
    :param mdt_id: MDT instance id
    :return: List of GELIR cases
    '''

    gel_ir_list = GELInterpretationReport.objects.latest_cases_by_sample_type(
        sample_type=sample_type
    )
    mdt_instance = MDT.objects.get(id=mdt_id)
    mdt_reports = MDTReport.objects.filter(MDT=mdt_instance)
    reports_in_mdt = mdt_reports.values_list('interpretation_report', flat=True)
    report_filter = ReportFilter(request.GET, queryset=gel_ir_list)
    return render(request, 'gel2mdt/mdt_ir_select.html', {'gel_ir_list': gel_ir_list,
                                                          'report_filter': report_filter,
                                                          'mdt_id': mdt_id,
                                                           'mdt_reports': mdt_reports,
                                                          'reports_in_mdt': reports_in_mdt,
                                                          'sample_type': sample_type})


@login_required
def add_ir_to_mdt(request, mdt_id, irreport_id):
    """
    Adds a GELInterpretation report to a MDT
    :param request:
    :param mdt_id: MDT Instance ID
    :param irreport_id: GelIR ID
    :return: Add this report to the MDT
    """
    if request.method == 'POST':
        mdt_instance = MDT.objects.get(id=mdt_id)
        report_instance = GELInterpretationReport.objects.get(id=irreport_id)
        linkage_instance = MDTReport(interpretation_report=report_instance,
                                     MDT=mdt_instance)
        linkage_instance.save()

        proband_variants = ProbandVariant.objects.filter(interpretation_report=report_instance)
        for pv in proband_variants:
            if mdt_instance.sample_type == 'raredisease':
                pv.create_rare_disease_report()
            elif mdt_instance.sample_type == 'cancer':
                pv.create_cancer_report()

        return HttpResponseRedirect(f'/{mdt_instance.sample_type}/edit_mdt/{mdt_id}')


@login_required
def remove_ir_from_mdt(request, mdt_id, irreport_id):
    """
    Removes a proband from an MDT
    :param request:
    :param mdt_id: MDT ID
    :param irreport_id: GELIR ID
    :return: Removes this report from the MDT
    """
    if request.method=='POST':
        mdt_instance = MDT.objects.get(id=mdt_id)
        report_instance = GELInterpretationReport.objects.get(id=irreport_id)

        MDTReport.objects.filter(MDT=mdt_instance, interpretation_report=report_instance).delete()
        return HttpResponseRedirect(f'/{mdt_instance.sample_type}/edit_mdt/{mdt_id}')


@login_required
def mdt_view(request, mdt_id):
    """
    Main MDT view where users see the cases added to MDT
    :param request:
    :param mdt_id: MDT ID
    :return: Main MDT page
    """
    clinician = False
    clinicians_emails = Clinician.objects.all().values_list('email', flat=True)
    if request.user.email in clinicians_emails:
        clinician = True

    mdt_instance = MDT.objects.get(id=mdt_id)
    report_list = MDTReport.objects.filter(MDT=mdt_instance).values_list('interpretation_report', flat=True)
    reports = GELInterpretationReport.objects.filter(id__in=report_list)

    proband_variants = ProbandVariant.objects.filter(interpretation_report__in=report_list)
    proband_variant_count = {}
    t3_proband_variant_count = {}
    for report in reports:
        proband_variant_count[report.id] = 0
        t3_proband_variant_count[report.id] = 0
        pvs = ProbandVariant.objects.filter(interpretation_report=report)
        for pv in pvs:
            if pv.pvflag_set.all() and pv.max_tier == None:
                proband_variant_count[report.id] += 1
            if pv.max_tier:
                if pv.pvflag_set.all() or pv.max_tier < 3:
                    proband_variant_count[report.id] += 1
                else:
                    t3_proband_variant_count[report.id] += 1

    mdt_form = MdtForm(instance=mdt_instance)
    clinicians = Clinician.objects.filter(mdt=mdt_id).values_list('name', flat=True)
    clinical_scientists = ClinicalScientist.objects.filter(mdt=mdt_id).values_list('name', flat=True)
    other_staff = OtherStaff.objects.filter(mdt=mdt_id).values_list('name', flat=True)

    attendees = list(clinicians) + list(clinical_scientists) + list(other_staff)
    if mdt_form["status"].value() == "C":
        for field in mdt_form.__dict__["fields"]:
            mdt_form.fields[field].widget.attrs['readonly'] = True
            mdt_form.fields[field].widget.attrs['disabled'] = True

    if request.method == 'POST':
        mdt_form = MdtForm(request.POST, instance=mdt_instance)

        if mdt_form.is_valid():
            mdt_form.save()
            messages.add_message(request, 25, 'MDT Updated')

        return HttpResponseRedirect(f'/mdt_view/{mdt_id}')
    request.session['mdt_id'] = mdt_id
    return render(request, 'gel2mdt/mdt_view.html', {'proband_variants': proband_variants,
                                                      'proband_variant_count': proband_variant_count,
                                                     't3_proband_variant_count': t3_proband_variant_count,
                                                      'reports': reports,
                                                      'mdt_form': mdt_form,
                                                      'mdt_id': mdt_id,
                                                      'attendees': attendees,
                                                     'sample_type': mdt_instance.sample_type,
                                                     'clinician': clinician})


@login_required
def mdt_proband_view(request, mdt_id, pk, important):
    '''
    MDT proband view where users can edit proband specific questions at MDT
    :param request:
    :param mdt_id: MDT instance id
    :param pk: GEL Interpretation report id
    :param important: Either 1 or 0; Whether to display T3 or non T3 variants
    :return:
    '''
    clinician = False
    clinicians_emails = Clinician.objects.all().values_list('email', flat=True)
    if request.user.email in clinicians_emails:
        clinician = True
    mdt_instance = MDT.objects.get(id=mdt_id)
    report = GELInterpretationReport.objects.get(id=pk)
    proband_variants = []
    proband_variants_all = ProbandVariant.objects.filter(interpretation_report=report)
    for pv in proband_variants_all:
        if important ==1:
            if pv.pvflag_set.all() or pv.max_tier < 3:
                proband_variants.append(pv)
        else:
            if not pv.pvflag_set.all():
                proband_variants.append(pv)

    for pv in proband_variants:
        if mdt_instance.sample_type == 'raredisease':
            pv.create_rare_disease_report()
        elif mdt_instance.sample_type == 'cancer':
            pv.create_cancer_report()

    if mdt_instance.sample_type == 'raredisease':
        proband_variant_reports = RareDiseaseReport.objects.filter(proband_variant__in=proband_variants)
        VariantForm = modelformset_factory(RareDiseaseReport, form=RareDiseaseMDTForm, extra=0)
    elif mdt_instance.sample_type == 'cancer':
        proband_variant_reports = CancerReport.objects.filter(proband_variant__in=proband_variants)
        VariantForm = modelformset_factory(CancerReport, form=CancerMDTForm, extra=0)
    variant_formset = VariantForm(queryset=proband_variant_reports)

    proband_form = ProbandMDTForm(instance=report.ir_family.participant_family.proband)
    gelir_form = GELIRMDTForm(instance=report)
    panels = InterpretationReportFamilyPanel.objects.filter(ir_family=report.ir_family)

    if mdt_instance.status == "C":
        for form in variant_formset.forms:
            for field in form.__dict__["fields"]:
                form.fields[field].widget.attrs['readonly'] = True
                form.fields[field].widget.attrs['disabled'] = True
        for field in proband_form.__dict__["fields"]:
            proband_form.fields[field].widget.attrs['readonly'] = True
            proband_form.fields[field].widget.attrs['disabled'] = True

    if request.method == 'POST':
        variant_formset = VariantForm(request.POST)
        proband_form = ProbandMDTForm(request.POST, instance=report.ir_family.participant_family.proband)
        gelir_form = GELIRMDTForm(request.POST, instance=report)
        if variant_formset.is_valid() and proband_form.is_valid() and gelir_form.is_valid():
            variant_formset.save()
            for form in variant_formset:
                pv = form.instance.proband_variant
                pv.validation_status = form.cleaned_data['requires_validation']
                pv.save()
            proband_form.save()
            gelir_form.save()
            messages.add_message(request, 25, 'Proband Updated')

        return HttpResponseRedirect(f'/mdt_proband_view/{mdt_id}/{pk}/{important}')

    for form in variant_formset:
        pv = form.instance.proband_variant
        form.initial["requires_validation"] = pv.validation_status
    return render(request, 'gel2mdt/mdt_proband_view.html', {
        'proband_variants': proband_variants,
        'report': report,
        'mdt_id': mdt_id,
        'mdt_instance': mdt_instance,
        'proband_form': proband_form,
        'variant_formset': variant_formset,
        'panels': panels,
        'sample_type':report.sample_type,
        'gelir_form':gelir_form,
        'clinician': clinician
    })


@login_required
def edit_mdt_proband(request, report_id):
    """
    Used for modal at MDT view to edit proband specific discussion and actions
    :param request:
    :param report_id: GEL IR id
    :return: Edits the proband discussion and actions in the MDT
    """
    data = {}
    report = GELInterpretationReport.objects.get(id=report_id)
    if request.method == 'POST':
        proband_form = ProbandMDTForm(request.POST,
                                      instance=report.ir_family.participant_family.proband)
        mdt_id = request.session.get('mdt_id')
        if proband_form.is_valid():
            proband_form.save()
            data['form_is_valid'] = True

            report_list = MDTReport.objects.filter(MDT=mdt_id).values_list('interpretation_report', flat=True)
            reports = GELInterpretationReport.objects.filter(id__in=report_list)
            proband_variant_count = {}
            t3_proband_variant_count = {}
            for report in reports:
                proband_variant_count[report.id] = 0
                t3_proband_variant_count[report.id] = 0
                pvs = ProbandVariant.objects.filter(interpretation_report=report)
                for pv in pvs:
                    if pv.pvflag_set.all() or pv.max_tier < 3:
                        proband_variant_count[report.id] += 1
                    else:
                        t3_proband_variant_count[report.id] += 1

            data['html_mdt_list'] = render_to_string('gel2mdt/includes/mdt_proband_table.html', {
                'reports': reports,
                'proband_variant_count': proband_variant_count,
                't3_proband_variant_count': t3_proband_variant_count,
                'mdt_id': request.session['mdt_id']
            })
        else:
            data['form_is_valid'] = False
            print(proband_form.errors)
    else:
        proband_form = ProbandMDTForm(instance=report.ir_family.participant_family.proband)

    context = {'proband_form': proband_form,
               'report': report}

    html_form = render_to_string('gel2mdt/modals/mdt_proband_form.html',
                                 context,
                                 request=request,
                                 )
    data['html_form'] = html_form
    return JsonResponse(data)


@login_required
def recent_mdts(request, sample_type):
    '''
    Shows table of recent MDTs
    :param request:
    :param sample_type: Either cancer or raredisease
    :return: A list of cancer or raredisease MDTs
    '''
    clinician = False
    clinicians_emails = Clinician.objects.all().values_list('email', flat=True)
    if request.user.email in clinicians_emails:
        clinician = True
    recent_mdt = list(MDT.objects.filter(sample_type=sample_type).order_by('-date_of_mdt'))
    config_dict = load_config.LoadConfig().load()
    # Need to get which probands were in MDT
    probands_in_mdt = {}
    for mdt in recent_mdt:
        probands_in_mdt[mdt.id] = []
        report_list = MDTReport.objects.filter(MDT=mdt.id)
        for report in report_list:
            if config_dict['cip_as_id'] == 'True':
                probands_in_mdt[mdt.id].append((report.interpretation_report.id,
                                                report.interpretation_report.ir_family.ir_family_id))
            else:
                probands_in_mdt[mdt.id].append((report.interpretation_report.id,
                                            report.interpretation_report.ir_family.participant_family.proband.gel_id))

    return render(request, 'gel2mdt/recent_mdts.html', {'recent_mdt': recent_mdt,
                                                        'probands_in_mdt': probands_in_mdt,
                                                        'sample_type': sample_type,
                                                        'clinician': clinician})


@login_required
def delete_mdt(request, mdt_id):
    '''
    Deletes a selected MDT
    :param request:
    :param mdt_id: MDT ID
    :return: Back to recent MDTs
    '''
    if request.method == "POST":
        mdt_instance = MDT.objects.get(id=mdt_id)
        # Delete existing entrys in MDTReport:
        MDTReport.objects.filter(MDT=mdt_instance).delete()
        mdt_instance.delete()
        messages.error(request, 'MDT Deleted')
    return HttpResponseRedirect(f'/{mdt_instance.sample_type}/recent_mdts')


@login_required
def select_attendees_for_mdt(request, mdt_id):
    '''
    Adds a CS/Clinician/Other to a MDT
    :param request:
    :param mdt_id: MDT ID
    :return: Table showing all users
    '''
    clinicians = (Clinician.objects.filter(added_by_user=True)
                  .values('name', 'email', 'hospital', 'id', 'mdt')
                  .distinct())
    clinical_scientists = (ClinicalScientist.objects.all()
                           .values('name', 'email', 'hospital', 'id', 'mdt')
                           .distinct())
    other_staff = (OtherStaff.objects.all()
                       .values('name', 'email', 'hospital', 'id', 'mdt')
                       .distinct())
    for clinician in clinicians:
        clinician['role'] = 'Clinician'
    for cs in clinical_scientists:
        cs['role'] = 'Clinical Scientist'
    for other in other_staff:
        other['role'] = 'Other Staff'
    attendees = list(clinicians) + list(clinical_scientists) + list(other_staff)
    currently_added_to_mdt = []
    for attendee in attendees:
        if attendee['mdt'] == mdt_id:
            currently_added_to_mdt.append(attendee['email'])
        attendee.pop('mdt')

    attendees = [dict(y) for y in set(tuple(x.items()) for x in attendees)]
    request.session['mdt_id'] = mdt_id
    return render(request, 'gel2mdt/select_attendee_for_mdt.html', {'attendees': attendees, 'mdt_id': mdt_id,
                                                                    'currently_added_to_mdt': currently_added_to_mdt})


@login_required
def add_attendee_to_mdt(request, mdt_id, attendee_id, role):
    '''
    Adds a attendee to a MDT
    :param request:
    :param mdt_id: MDT instance id
    :param attendee_id: Attendee ID
    :param role: Either Clinician, Clinical Scientist or Other Staff
    :return: To view where users can add attendees
    '''
    if request.method == 'POST':
        mdt_instance = MDT.objects.get(id=mdt_id)

        if role == 'Clinician':
            clinician = Clinician.objects.get(id=attendee_id)
            mdt_instance.clinicians.add(clinician)
            mdt_instance.save()
        elif role == 'Clinical Scientist':
            clinical_scientist = ClinicalScientist.objects.get(id=attendee_id)
            mdt_instance.clinical_scientists.add(clinical_scientist)
            mdt_instance.save()
        elif role == 'Other Staff':
            other = OtherStaff.objects.get(id=attendee_id)
            mdt_instance.other_staff.add(other)
            mdt_instance.save()
        return HttpResponseRedirect(f'/select_attendees_for_mdt/{mdt_id}')


@login_required
def remove_attendee_from_mdt(request, mdt_id, attendee_id, role):
    '''
    Removes a attendee from an MDT
    :param request:
    :param mdt_id: MDT instance id
    :param attendee_id: Attendee ID
    :param role: Either Clinician, Clinical Scientist or Other Staff
    :return: To view where users can add attendees
    '''
    if request.method == 'POST':
        mdt_instance = MDT.objects.get(id=mdt_id)
        if role == 'Clinician':
            clinician = Clinician.objects.get(id=attendee_id)
            mdt_instance.clinicians.remove(clinician)
        elif role == 'Clinical Scientist':
            clinical_scientist = ClinicalScientist.objects.get(id=attendee_id)
            mdt_instance.clinical_scientists.remove(clinical_scientist)
        elif role == 'Other Staff':
            other = OtherStaff.objects.get(id=attendee_id)
            mdt_instance.other_staff.remove(other)
        return HttpResponseRedirect(f'/select_attendees_for_mdt/{mdt_id}')


@login_required
def add_new_attendee(request):
    '''
    Add a new attendee to the 3 attendee models
    :param request:
    :return: Either to select attendees view if mdt_id in request.session or back to index if not
    '''
    if request.method == 'POST':

        form = AddNewAttendee(request.POST)
        if form.is_valid():
            if form.cleaned_data['role'] == 'Clinician':
                clinician, created = Clinician.objects.get_or_create(
                                      email=form.cleaned_data['email'])
                clinician.name=form.cleaned_data['name']
                clinician.hospital=form.cleaned_data['hospital']
                clinician.added_by_user=True
                clinician.save()
            elif form.cleaned_data['role'] == 'Clinical Scientist':
                cs, created = ClinicalScientist.objects.get_or_create(
                                       email=form.cleaned_data['email'])
                cs.name = form.cleaned_data['name']
                cs.hospital = form.cleaned_data['hospital']
                cs.save()
            elif form.cleaned_data['role'] == 'Other Staff':
                other, created = OtherStaff.objects.get_or_create(
                                   email=form.cleaned_data['email'])
                other.name = form.cleaned_data['name']
                other.hospital = form.cleaned_data['hospital']
                other.save()
            messages.add_message(request, 25, 'Attendee Added')
            if 'mdt_id' in request.session:
                return HttpResponseRedirect('/select_attendees_for_mdt/{}'.format(request.session.get('mdt_id')))
            else:
                return redirect('index')

    else:
        form = AddNewAttendee()
    return render(request, 'gel2mdt/add_new_attendee.html', {'form': form})


@login_required
def export_mdt(request, mdt_id):
    '''
    Returns MDT information in CSV format
    :param request:
    :param mdt_id: MDT instance
    :return: CSV file
    '''
    if request.method == "POST":
        mdt_instance = MDT.objects.get(id=mdt_id)
        mdt_reports = MDTReport.objects.filter(MDT=mdt_instance)
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename=MDT_{}.csv'.format(mdt_id)
        writer = csv.writer(response)
        writer = write_mdt_export(writer, mdt_instance, mdt_reports)
        return response


@login_required
def export_mdt_outcome_form(request, report_id):
    '''
    Exports MDT outcome form which is proband specific after a case has been to MDT
    :param request:
    :param report_id:  GEL Interpretation report
    :return: DOCX format file
    '''
    report = GELInterpretationReport.objects.get(id=report_id)
    document, mdt = write_mdt_outcome_template(report)
    f = BytesIO()
    document.save(f)
    length = f.tell()
    f.seek(0)
    response = HttpResponse(
        f.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )

    filename = '{}_{}_{}_{}.docx'.format(report.ir_family.participant_family.proband.surname,
                                         report.ir_family.participant_family.proband.forename,
                                         report.ir_family.ir_family_id,
                                         mdt.date_of_mdt.date())
    response['Content-Disposition'] = 'attachment; filename=' + filename
    response['Content-Length'] = length
    return response

@login_required
def export_gtab_template(request, report_id):
    '''
    Exports MDT outcome form which is proband specific after a case has been to MDT
    :param request:
    :param report_id:  GEL Interpretation report
    :return: DOCX format file
    '''
    report = GELInterpretationReport.objects.get(id=report_id)
    document = write_gtab_template(report)
    f = BytesIO()
    document.save(f)
    length = f.tell()
    f.seek(0)
    response = HttpResponse(
        f.getvalue(),
        content_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )

    filename = '{}_{}_{}.docx'.format(report.ir_family.participant_family.proband.surname,
                                         report.ir_family.participant_family.proband.forename,
                                         report.ir_family.ir_family_id,)
    response['Content-Disposition'] = 'attachment; filename=' + filename
    response['Content-Length'] = length
    return response


@login_required
def report(request, report_id, outcome):
    '''
    Printer friendly negative report template
    :param request:
    :param report_id: GEL Report ID
    :return:
    '''
    config_dict = load_config.LoadConfig().load()

    report = GELInterpretationReport.objects.get(id=report_id)
    genome_build = report.assembly
    panels = InterpretationReportFamilyPanel.objects.filter(ir_family=report.ir_family)

    panel_genes = {}
    for panel in panels:
        panelapp_file = f'{config_dict["panelapp_storage"]}/{panel.panel.panel.panelapp_id}_{panel.panel.version_number}.json'
        if os.path.isfile(panelapp_file):
            panelapp_json = json.load(open(panelapp_file))
            green_genes = [gene for gene in panelapp_json['result']['Genes']
                         if gene['LevelOfConfidence'] == "HighEvidence"]
            panel_genes[panel] = len(green_genes)
        else:
            panel_genes[panel] = ''

    if outcome == "positive":
        reported_variant_ids = request.GET.getlist('rdr')
        reported_variants = RareDiseaseReport.objects.filter(
            id__in=reported_variant_ids
        )
    else:
        reported_variants = None

    return render_to_pdf_response(
        request=request,
        template='gel2mdt/technical_information.html',
        context={
            'outcome': outcome,
            'build': genome_build,
            'report': report,
            'reported_variants': reported_variants,
            'panels': panel_genes
        }
    )


@login_required
def genomics_england_report(request, report_id):
    """
    Sends the genomics england report to the users email address
    :param report_id: GELInterpretation Report iD
    :return Back to proband page
    """
    report = GELInterpretationReport.objects.get(id=report_id)
    cip_id = report.ir_family.ir_family_id.split('-')
    try:
        gel_content = get_gel_content(cip_id[0], cip_id[1])
    except:
        messages.add_message(request, 40, 'Not successful, please contact bioinformatics about this')
        return HttpResponseRedirect(f'/proband/{report_id}')
    return render(request, 'gel2mdt/gel_template.html', {'gel_content': gel_content})


@login_required
def audit(request, sample_type):
    '''
    Create figures giving breakdown of case status and NPF cases
    :param request:
    :param sample_type: Choice of raredisease and cancer
    :return:
    '''
    config_dict = load_config.LoadConfig().load()
    # Getting all GELIRs
    qs = GELInterpretationReport.objects.filter(
        sample_type=sample_type).prefetch_related(*['ir_family', 'ir_family__participant_family__proband'])

    # Filtering out duplicates
    qs_df = pd.DataFrame(list(qs.values())).sort_values(by=['ir_family_id', 'archived_version'])
    multi_archived = qs_df.drop_duplicates(subset=['ir_family_id'], keep='last')
    ids_of_latest = multi_archived["id"].tolist()
    queryset = GELInterpretationReport.objects.filter(id__in=ids_of_latest).filter(~Q(status='blocked'))

    # Getting case status options
    status_choices = dict(GELInterpretationReport._meta.get_field('case_status').choices)
    status_names = list(status_choices.values())

    # Total case breakdown
    if config_dict['plot_pilot_and_main_status_breakdown'] == 'False':
        case_status_breakdown = queryset.values(
            'case_status').annotate(Count('case_status'))
        case_status_breakdown = {item['case_status']: item['case_status__count'] for item in case_status_breakdown}
        status_counts = [case_status_breakdown.get(f, 0) for f in status_choices]
        plots = create_bokeh_barplot(status_names, status_counts, 'Total Status Count')

    else:
        # Main study status plot
        case_status_breakdown = queryset.filter(sample_type=sample_type, pilot_case=False).values(
            'case_status').annotate(Count('case_status'))
        case_status_breakdown = {item['case_status']: item['case_status__count'] for item in case_status_breakdown}
        status_counts = [case_status_breakdown.get(f, 0) for f in status_choices]
        main_study_count_plot = create_bokeh_barplot(status_names, status_counts, 'Main Study Status Count')

        # Pilot study status plot
        case_status_breakdown = queryset.filter(sample_type=sample_type, pilot_case=True).values(
            'case_status').annotate(Count('case_status'))
        case_status_breakdown = {item['case_status']: item['case_status__count'] for item in case_status_breakdown}
        status_counts = [case_status_breakdown.get(f, 0) for f in status_choices]
        pilot_study_count_plot = create_bokeh_barplot(status_names, status_counts, 'Pilot Study Status Count')
        plots = row([main_study_count_plot, pilot_study_count_plot])
    script, div = components(plots, CDN)
    return render(request, 'gel2mdt/audit.html', {'script': script,
                  'div': div, 'sample_type': sample_type})


@login_required
def case_alert(request, sample_type):
    '''
    Shows a list of cases which have an alert on them
    :param request:
    :param sample_type:
    :return:
    '''
    case_alerts = CaseAlert.objects.filter(sample_type=sample_type)
    gel_reports = GELInterpretationReport.objects.latest_cases_by_sample_type(
        sample_type=sample_type).prefetch_related('ir_family__participant_family__proband')
    matching_cases = {}
    case_alert_form = AddCaseAlert()
    for case in case_alerts:
        matching_cases[case.id] = []
        for report in gel_reports:
            try:
                if report.ir_family.participant_family.proband.gel_id == str(case.gel_id):
                    matching_cases[case.id].append((report.id,
                                                    report.ir_family.ir_family_id))
            except Proband.DoesNotExist:
                pass

    return render(request, 'gel2mdt/case_alert.html', {'case_alerts': case_alerts,
                                                       'matching_cases': matching_cases,
                                                       'sample_type': sample_type,
                                                       'case_alert_form': case_alert_form})


@login_required
def add_case_alert(request):
    if request.method == 'POST':
        case_alert_form = AddCaseAlert(request.POST)
        if case_alert_form.is_valid():
            case_alert_form.save()
            messages.add_message(request, 25, 'Case Added!')
        else:
            messages.add_message(request, 40, 'Not successful, is the GELID correct?')
    return redirect('case-alert', sample_type=case_alert_form.cleaned_data['sample_type'])


@login_required
def edit_case_alert(request, case_alert_id):
    data = {}
    case_alert_instance = CaseAlert.objects.get(id=case_alert_id)
    case_alert_form = AddCaseAlert(instance=case_alert_instance)
    if request.method == 'POST':
        case_alert_form = AddCaseAlert(request.POST, instance=case_alert_instance)
        if case_alert_form.is_valid():
            case_alert_form.save()
            data['form_is_valid'] = True
        return redirect('case-alert', sample_type=case_alert_instance.sample_type)
    context = {'case_alert_form': case_alert_form, 'case_alert_instance': case_alert_instance}
    html_form = render_to_string('gel2mdt/modals/case_alert_modal.html', context, request=request)
    data['html_form'] = html_form
    return JsonResponse(data)


@login_required
def delete_case_alert(request, case_alert_id):
    case_alert_instance = CaseAlert.objects.get(id=case_alert_id)
    sample_type = case_alert_instance.sample_type
    case_alert_instance.delete()
    messages.add_message(request, 25, 'Alert Deleted')
    return redirect('case-alert', sample_type=sample_type)