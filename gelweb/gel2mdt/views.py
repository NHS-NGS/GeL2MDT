from django.shortcuts import render
from .forms import *
from .models import *
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from datetime import datetime
from django.template.loader import render_to_string
from django.http import JsonResponse
from django.db.models import Q
from .database_utils.multiple_case_adder import MultipleCaseAdder

# Create your views here.
def register(request):
    '''
    Registers a new user
    :param request:
    :return:
    '''
    registered = False
    username = ''

    if request.method == 'POST':
        user_form = UserForm(data=request.POST)

        if user_form.is_valid():
            first_name = user_form.cleaned_data['first_name']
            last_name = user_form.cleaned_data['last_name']
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
                if role == 'CS':
                    cs = ClinicalScientist(name=first_name + ' ' + last_name,
                                           email=email,
                                           hospital=hospital)
                    cs.save()
                elif role == 'Clinician':
                    clinician = Clinician(name=first_name + ' ' + last_name,
                                          email=email,
                                          hospital=hospital)
                    clinician.save()
                elif role == 'Other':
                    other = OtherStaff(name=first_name + ' ' + last_name,
                                       email=email,
                                       hospital=hospital)
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
def index(request):
    '''
    Gives the user the choice between rare disease and cancer
    :param request:
    :return:
    '''
    # We want this to be a choice between cancer and rare disease
    return render(request, 'gel2mdt/index.html', {})

@login_required
def cancer_main(request):
    '''
    Shows all the Cancer cases the user has access to and allows easy searching of cases
    :param request:
    :return:
    '''
    return render(request, 'gel2mdt/cancer_main.html', {})

@login_required
def rare_disease_main(request):
    '''
    Shows all the RD cases the user has access to and allows easy searching of cases
    :param request:
    :return:
    '''

    #create_dummy_sample()

    if request.method == "POST":
        if request.POST.get("cases") == 'live':
            update = MultipleCaseAdder()
        elif request.POST.get("cases") == 'test':
            update = MultipleCaseAdder(test_data=True)

    rd_cases = GELInterpretationReport.objects.all()
    return render(request, 'gel2mdt/rare_disease_main.html', {'rd_cases': rd_cases})

@login_required
def main_cases(request):
    '''
    Shows breakdown of GEL main cases in database by proband status
    :param request:
    :return:
    '''
    not_started = GELInterpretationReport.objects.filter(ir_family__participant_family__proband__status='N').\
        filter(~Q(ir_family__participant_family__proband__pilot_case=True))
    completed = GELInterpretationReport.objects.filter(ir_family__participant_family__proband__status='C'). \
        filter(~Q(ir_family__participant_family__proband__pilot_case=True))
    awaiting_mdt = GELInterpretationReport.objects.filter(ir_family__participant_family__proband__status='M'). \
        filter(~Q(ir_family__participant_family__proband__pilot_case=True))
    under_review = GELInterpretationReport.objects.filter(ir_family__participant_family__proband__status='U'). \
        filter(~Q(ir_family__participant_family__proband__pilot_case=True))
    awaiting_reporting = GELInterpretationReport.objects.filter(ir_family__participant_family__proband__status='R'). \
        filter(~Q(ir_family__participant_family__proband__pilot_case=True))
    awaiting_validation = GELInterpretationReport.objects.filter(ir_family__participant_family__proband__status='V'). \
        filter(~Q(ir_family__participant_family__proband__pilot_case=True))
    reported = GELInterpretationReport.objects.filter(ir_family__participant_family__proband__status='P'). \
        filter(~Q(ir_family__participant_family__proband__pilot_case=True))
    external = GELInterpretationReport.objects.filter(ir_family__participant_family__proband__status='E'). \
        filter(~Q(ir_family__participant_family__proband__pilot_case=True))

    reports_previously_in_mdt = MDTReport.objects.all().values_list('interpretation_report', flat=True).distinct()
    return render(request, 'gel2mdt/main_cases.html', {'not_started': not_started,
                                                          'completed': completed,
                                                          'awaiting_mdt': awaiting_mdt,
                                                          'awaiting_validation': awaiting_validation,
                                                          'awaiting_reporting': awaiting_reporting,
                                                          'reported': reported,
                                                          'under_review': under_review,
                                                          'reports_previously_in_mdt': reports_previously_in_mdt,
                                                          'external': external})


@login_required
def pilot_cases(request):
    '''
    Split the pilot cases by proband status
    :param request:
    :return:
    '''
    not_started = GELInterpretationReport.objects.filter(ir_family__participant_family__proband__status='N'). \
        filter(ir_family__participant_family__proband__pilot_case=True)
    completed = GELInterpretationReport.objects.filter(ir_family__participant_family__proband__status='C'). \
        filter(ir_family__participant_family__proband__pilot_case=True)
    awaiting_mdt = GELInterpretationReport.objects.filter(ir_family__participant_family__proband__status='M'). \
        filter(ir_family__participant_family__proband__pilot_case=True)
    under_review = GELInterpretationReport.objects.filter(ir_family__participant_family__proband__status='U'). \
        filter(ir_family__participant_family__proband__pilot_case=True)
    awaiting_reporting = GELInterpretationReport.objects.filter(ir_family__participant_family__proband__status='R'). \
        filter(ir_family__participant_family__proband__pilot_case=True)
    awaiting_validation = GELInterpretationReport.objects.filter(ir_family__participant_family__proband__status='V'). \
        filter(ir_family__participant_family__proband__pilot_case=True)
    reported = GELInterpretationReport.objects.filter(ir_family__participant_family__proband__status='P'). \
        filter(ir_family__participant_family__proband__pilot_case=True)
    external = GELInterpretationReport.objects.filter(ir_family__participant_family__proband__status='E'). \
        filter(ir_family__participant_family__proband__pilot_case=True)

    reports_previously_in_mdt = MDTReport.objects.all().values_list('interpretation_report', flat=True).distinct()
    return render(request, 'gel2mdt/pilot_cases.html', {'not_started': not_started,
                                                           'completed': completed,
                                                           'awaiting_mdt': awaiting_mdt,
                                                           'awaiting_validation': awaiting_validation,
                                                           'awaiting_reporting': awaiting_reporting,
                                                           'reported': reported,
                                                           'under_review': under_review,
                                                           'reports_previously_in_mdt': reports_previously_in_mdt,
                                                           'external': external})


@login_required
def proband_view(request, report_id):
    '''
    Shows details about a particular proband, some fields are editable by clinical scientists
    :param request:
    :param report_id: GEL Report ID
    :return:
    '''
    report = GELInterpretationReport.objects.get(id=report_id)
    relatives = Relative.objects.filter(proband=report.ir_family.participant_family.proband)
    proband_form = ProbandForm(instance=report.ir_family.participant_family.proband)
    proband_transcript_variant = ProbandTranscriptVariant.objects.filter(proband_variant__interpretation_report=report,
                                                                         selected=True)

    proband_mdt = MDTReport.objects.filter(interpretation_report=report)
    return render(request, 'gel2mdt/proband.html', {'report': report,
                                                    'relatives': relatives,
                                                    'proband_form': proband_form,
                                                    'proband_transcript_variant': proband_transcript_variant,
                                                    'proband_mdt': proband_mdt})

@login_required
def update_proband(request, report_id):
    '''
    Updates the Proband page
    :param request:
    :param report_id: GEL Report ID
    :return:
    '''
    report = GELInterpretationReport.objects.get(id=report_id)
    if request.method == "POST":
        proband_form = ProbandForm(request.POST, instance=report.ir_family.participant_family.proband)

        if proband_form.is_valid():
            proband_form.save()
            messages.add_message(request, 25, 'Proband Updated')
            return HttpResponseRedirect(f'/proband/{report_id}')

@login_required
def select_transcript(request, report_id, pv_id):
    '''
    Shows the transcript table and allows a user to select preferred transcript
    :param request:
    :param pv_id:
    :return:
    '''
    proband_transcript_variants = ProbandTranscriptVariant.objects.filter(proband_variant__id=pv_id)
    report = GELInterpretationReport.objects.get(id=report_id)
    return render(request, 'gel2mdt/select_transcript.html',
                  {'proband_transcript_variants': proband_transcript_variants,
                   'report': report})

@login_required
def update_transcript(request, report_id, pv_id, transcript_id):
    '''
    Updates the selected transcript
    :param request:
    :param pv_id:
    :return:
    '''
    transcript = Transcript.objects.get(id=transcript_id)
    proband_variant = ProbandVariant.objects.get(id=pv_id)
    proband_variant.select_transcript(selected_transcript=transcript)
    return HttpResponseRedirect(f'/select_transcript/{report_id}/{proband_variant.id}')

@login_required
def start_mdt_view(request):
    '''
    Creates a new MDT instance
    :param request:
    :return:
    '''
    mdt_instance = MDT(creator=request.user.username, date_of_mdt=datetime.now())
    mdt_instance.save()

    return HttpResponseRedirect(f'/edit_mdt/{mdt_instance.id}')


@login_required
def edit_mdt(request, mdt_id):
    '''
    Allows users to select which cases they want to bring to MDT
    :param request:
    :param mdt_id:
    :return:
    '''

    gel_ir_list = GELInterpretationReport.objects.all()
    mdt_instance = MDT.objects.get(id=mdt_id)
    reports_in_mdt = MDTReport.objects.filter(MDT=mdt_instance).values_list('interpretation_report', flat=True)

    return render(request, 'gel2mdt/mdt_ir_select.html', {'gel_ir_list': gel_ir_list,
                                                          'reports_in_mdt': reports_in_mdt,
                                                          'mdt_id': mdt_id})


@login_required
def add_ir_to_mdt(request, mdt_id, irreport_id):
    """
    :param request:
    :param mdt_id: MDT ID
    :param irreport_id: GelIR ID
    :return: Add this report to the MDT
    """
    if request.method == 'POST':
        mdt_instance = MDT.objects.get(id=mdt_id)
        report_instance = GELInterpretationReport.objects.get(id=irreport_id)
        linkage_instance = MDTReport(interpretation_report=report_instance,
                                     MDT=mdt_instance)
        linkage_instance.save()
        return HttpResponseRedirect(f'/edit_mdt/{mdt_id}')


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
        return HttpResponseRedirect(f'/edit_mdt/{mdt_id}')


@login_required
def mdt_view(request, mdt_id):
    """
    :param request:
    :param mdt_id: MDT ID
    :return: Main MDT page
    """
    mdt_instance = MDT.objects.get(id=mdt_id)
    report_list = MDTReport.objects.filter(MDT=mdt_instance).values_list('interpretation_report', flat=True)
    reports = GELInterpretationReport.objects.filter(id__in=report_list)

    proband_transcript_variants = ProbandTranscriptVariant.objects.filter(
        proband_variant__interpretation_report__in=report_list, selected=True)
    mdt_form = MdtForm(instance=mdt_instance)
    clinicians = Clinician.objects.filter(mdt=mdt_id)
    clinical_scientists = ClinicalScientist.objects.filter(mdt=mdt_id)
    other_staff = OtherStaff.objects.filter(mdt=mdt_id)

    attendees = list(clinicians) + list(clinical_scientists) + list(other_staff)

    if request.method == 'POST':
        mdt_form = MdtForm(request.POST, instance=mdt_instance)

        if mdt_form.is_valid():
            mdt_form.save()
            messages.add_message(request, 25, 'MDT Updated')

        return HttpResponseRedirect(f'/mdt_view/{mdt_id}')
    request.session['mdt_id'] = mdt_id
    return render(request, 'gel2mdt/mdt_view2.html', {'proband_transcript_variants': proband_transcript_variants,
                                                      'reports': reports,
                                                      'mdt_form': mdt_form,
                                                      'mdt_id': mdt_id,
                                                      'attendees': attendees})

@login_required
def edit_mdt_variant(request, pv_id):
    """
    Edits the proband variants in the MDT
    :param request:
    :param pv_id: Proband Variant ID
    :return: Back to MDT view
    """
    data = {}
    proband_variant = ProbandVariant.objects.get(id=pv_id)
    mdt_id = request.session.get('mdt_id')
    if request.method == 'POST':
        modal_form = VariantMDTForm(request.POST, instance=proband_variant)
        if modal_form.is_valid():
            modal_form.save()
            data['form_is_valid'] = True

            report_list = MDTReport.objects.filter(MDT=mdt_id).values_list('interpretation_report', flat=True)

            proband_transcript_variants = ProbandTranscriptVariant.objects.filter(
                proband_variant__interpretation_report__in=report_list, selected=True)
            data['html_mdt_list'] = render_to_string('gel2mdt/includes/mdt_variant_table.html', {
                'proband_transcript_variants': proband_transcript_variants,
            })
        else:
            data['form_is_valid'] = False
            print(modal_form.errors)
    else:
        modal_form = VariantMDTForm(instance=proband_variant)
    context = {'modal_form': modal_form, 'pv_id': pv_id}
    html_form = render_to_string('gel2mdt/modals/mdt_variant_form.html',
                                 context,
                                 request=request,
                                 )
    data['html_form'] = html_form
    return JsonResponse(data)


@login_required
def edit_mdt_proband(request, proband_id):
    """
    :param request:
    :param pk: Sample ID
    :return: Edits the proband discussion and actions in the MDT
    """
    data = {}
    proband = Proband.objects.get(id=proband_id)
    if request.method == 'POST':
        proband_form = ProbandMDTForm(request.POST, instance=proband)
        mdt_id = request.session.get('mdt_id')
        if proband_form.is_valid():
            proband_form.save()
            data['form_is_valid'] = True

            report_list = MDTReport.objects.filter(MDT=mdt_id).values_list('interpretation_report', flat=True)
            reports = GELInterpretationReport.objects.filter(id__in=report_list)

            data['html_mdt_list'] = render_to_string('gel2mdt/includes/mdt_proband_table.html', {
                'reports': reports
            })
        else:
            data['form_is_valid'] = False
    else:
        proband_form = ProbandMDTForm(instance=proband)

    context = {'proband_form': proband_form, 'proband_id': proband_id}
    html_form = render_to_string('gel2mdt/modals/mdt_proband_form.html',
                                 context,
                                 request=request,
                                 )
    data['html_form'] = html_form
    return JsonResponse(data)

@login_required
def recent_mdts(request):
    '''
    Shows table of recent MDTs
    :param request:
    :return:
    '''
    recent_mdt = list(MDT.objects.all().order_by('-date_of_mdt'))

    # Need to get which probands were in MDT
    probands_in_mdt = {}
    for mdt in recent_mdt:
        probands_in_mdt[mdt.id] = []
        report_list = MDTReport.objects.filter(MDT=mdt.id)
        for report in report_list:
            probands_in_mdt[mdt.id].append((report.interpretation_report.id, report.interpretation_report.ir_family.participant_family.proband.gel_id))

    return render(request, 'gel2mdt/recent_mdts.html', {'recent_mdt': recent_mdt,
                                                        'probands_in_mdt': probands_in_mdt})


@login_required
def delete_mdt(request, mdt_id):
    '''
    Deletes a selected MDT
    :param request:
    :param mdt_id:
    :return: Back to recent MDTs
    '''
    if request.method == "POST":
        mdt_instance = MDT.objects.get(id=mdt_id)
        # Delete existing entrys in MDTReport:
        MDTReport.objects.filter(MDT=mdt_instance).delete()
        mdt_instance.delete()
        messages.error(request, 'MDT Deleted')
    return HttpResponseRedirect('/recent_mdts')

@login_required
def select_attendees_for_mdt(request, mdt_id):
    '''
    Adds a CS/Clinician/Other to a MDT
    :param request:
    :param mdt_id:
    :return: Table showing all users
    '''
    clinicians = Clinician.objects.all().values('name', 'email', 'hospital', 'id', 'mdt').distinct()
    clinical_scientists = ClinicalScientist.objects.all().values('name', 'email', 'hospital', 'id', 'mdt').distinct()
    other_staff = OtherStaff.objects.all().values('name', 'email', 'hospital', 'id', 'mdt').distinct()
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

    # Uniquify the set of dicts, needed because of the mdt many relationship in the 3 models
    attendees = [dict(y) for y in set(tuple(x.items()) for x in attendees)]
    request.session['mdt_id'] = mdt_id
    return render(request, 'gel2mdt/select_attendee_for_mdt.html', {'attendees': attendees, 'mdt_id': mdt_id,
                                                                    'currently_added_to_mdt': currently_added_to_mdt})

@login_required
def add_attendee_to_mdt(request, mdt_id, attendee_id, role):
    '''

    :param request:
    :param mdt_id:
    :param attendee_id:
    :return:
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

    :param request:
    :param mdt_id:
    :param attendee_id:
    :return:
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


def add_new_attendee(request):
    '''
    Add a new attendee to the 3 attendee models
    :param request:
    :return:
    '''
    if request.method == 'POST':

        form = AddNewAttendee(request.POST)
        if form.is_valid():
            if form.cleaned_data['role'] == 'Clinician':
                clinician = Clinician(name=form.cleaned_data['name'],
                                      hospital=form.cleaned_data['hospital'],
                                      email=form.cleaned_data['email'])
                clinician.save()
            elif form.cleaned_data['role'] == 'Clinical Scientist':
                cs = ClinicalScientist(name=form.cleaned_data['name'],
                                       hospital=form.cleaned_data['hospital'],
                                       email=form.cleaned_data['email'])
                cs.save()
            elif form.cleaned_data['role'] == 'Other Staff':
                other = OtherStaff(name=form.cleaned_data['name'],
                                   hospital=form.cleaned_data['hospital'],
                                   email=form.cleaned_data['email'])
                other.save()
            if 'mdt_id' in request.session:
                return HttpResponseRedirect('/select_attendees_for_mdt/{}'.format(request.session.get('mdt_id')))
            else:
                return HttpResponseRedirect('/recent_mdts/')
    else:
        form = AddNewAttendee()
    return render(request, 'gel2mdt/add_new_attendee.html', {'form': form})
