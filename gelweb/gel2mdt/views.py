from django.shortcuts import render
from .forms import *
from .models import *
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import IntegrityError
from .for_me_testing import create_dummy_sample
from django.forms import modelformset_factory
from .database_utils import multiple_case_adder
from django.db.models import Max
from datetime import datetime

# Create your views here.
def register(request):
    """ Registration view for all new users
    """
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
            except IntegrityError as e:
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
    # create_dummy_sample()
    rd_cases = Proband.objects.all()
    return render(request, 'gel2mdt/rare_disease_main.html', {'rd_cases': rd_cases})


@login_required
def proband_view(request, gel_id):
    '''
    Shows details about a particular proband, some fields may be editable
    :param request:
    :return:
    '''
    proband = Proband.objects.get(gel_id=gel_id)
    relatives = Relative.objects.filter(proband=proband)
    proband_form = ProbandForm(instance=proband)
    gel_ir = GELInterpretationReport.objects.filter(ir_family__participant_family=proband.family).order_by('-polled_at_datetime')[0]
    probandtranscriptvariants = ProbandTranscriptVariant.objects.filter(proband_variant__interpretation_report=gel_ir)
    return render(request, 'gel2mdt/proband.html', {'proband': proband,
                                                    'relatives': relatives,
                                                    'proband_form': proband_form,
                                                    'probandtranscriptvariants':probandtranscriptvariants})


@login_required
def update_proband(request, gel_id):
    proband = Proband.objects.get(gel_id=gel_id)
    if request.method == "POST":
        proband_form = ProbandForm(request.POST, instance=proband)

        if proband_form.is_valid():
            proband_form.save()
            messages.add_message(request, 25, 'Proband Updated')
            return HttpResponseRedirect('/proband/{}'.format(gel_id))


@login_required
def start_mdt_view(request):
    """Select Samples for MDT instance
    """
    mdt_instance = MDT(creator=request.user.username, date_of_mdt=datetime.now())
    mdt_instance.save()

    return HttpResponseRedirect('/edit_mdt/{}'.format(mdt_instance.id))


@login_required
def edit_mdt(request, mdt_id):
    """
    Allows users to Add/Remove samples from MDT instance
    """
    # Gets the max version of each report
    gel_ir_queryset = GELInterpretationReport.objects.all()

    # somehow need a list of samples to check whether they are in MDT
    report_in_mdt = MDTReport.objects.filter(MDT=MDT.objects.get(id=mdt_id)).values('report')
    reports_currently_in_mdt = []
    for report in report_in_mdt:
        reports_currently_in_mdt.append(report.proband_variant.interpretation_report.id)

    report_list = []
    for gel_ir in gel_ir_queryset:
        if hasattr(gel_ir.ir_family.participant_family, 'proband'):
            report_list.append(gel_ir)
    return render(request, 'gel2mdt/mdt_ir_select.html', {'report_list': report_list,
                                                          'reports_currently_in_mdt': reports_currently_in_mdt})


@login_required
def add_ir_to_mdt(request, mdt_id, sid):
    """
    :param request:
    :param pk: MDT ID
    :param sid: Gel Participant ID
    :return: Add this sample to the MDT
    """
    if request.method == 'POST':
        mdt_instance = MDT.objects.get(id=mdt_id)
        sample_instance = Gel_Sample_Info.objects.get(gel_participant_id=sid)
        linkage_instance = Gel_Mdt_linkage(gel_sample_id=sample_instance,
                 gel_mdt_id=mdt_instance)
        linkage_instance.save()
        return HttpResponseRedirect('/gel2me/edit_mdt/{}'.format(pk))


@login_required
def remove_ir_from_mdt(request, mdt_id, sid):
    """
    :param request:
    :param pk: MDT ID
    :param sid: Sample Gel Participant ID
    :return: Removes this sample from the MDT
    """
    if request.method=='POST':
        mdt_instance = Gel_Mdt.objects.get(id=pk)
        sample_instance = Gel_Sample_Info.objects.get(gel_participant_id=sid)

        Gel_Mdt_linkage.objects.filter(gel_mdt_id=mdt_instance, gel_sample_id=sample_instance).delete()
        return HttpResponseRedirect('/gel2me/edit_mdt/{}'.format(pk))




