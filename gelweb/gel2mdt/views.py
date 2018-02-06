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
    rd_cases = GELInterpretationReport.objects.all()
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
    # proband_mdts = MDTReport.
    return render(request, 'gel2mdt/proband.html', {'proband': proband,
                                                    'relatives': relatives,
                                                    'proband_form': proband_form,
                                                    'probandtranscriptvariants':probandtranscriptvariants})


@login_required
def update_proband(request, gel_id):
    '''
    Updates the Proband page
    :param request:
    :param gel_id:
    :return:
    '''
    proband = Proband.objects.get(gel_id=gel_id)
    if request.method == "POST":
        proband_form = ProbandForm(request.POST, instance=proband)

        if proband_form.is_valid():
            proband_form.save()
            messages.add_message(request, 25, 'Proband Updated')
            return HttpResponseRedirect('/proband/{}'.format(gel_id))


@login_required
def start_mdt_view(request):
    '''
    Creates a new MDT instance
    :param request:
    :return:
    '''
    mdt_instance = MDT(creator=request.user.username, date_of_mdt=datetime.now())
    mdt_instance.save()

    return HttpResponseRedirect('/edit_mdt/{}'.format(mdt_instance.id))


@login_required
def edit_mdt(request, mdt_id):
    '''
    Allows users to select which cases they want to bring to MDT
    :param request:
    :param mdt_id:
    :return:
    '''
    # Gets the max version of each report
    gel_ir_queryset = GELInterpretationReport.objects.all()

    # somehow need a list of samples to check whether they are in MDT
    mdt_instance = MDT.objects.get(id=mdt_id)
    reports_in_mdt = MDTReport.objects.filter(MDT=mdt_instance).values_list('interpretation_report', flat=True)
    report_list = []
    for gel_ir in gel_ir_queryset:
        if hasattr(gel_ir.ir_family.participant_family, 'proband'):
            report_list.append(gel_ir)
    return render(request, 'gel2mdt/mdt_ir_select.html', {'report_list': report_list,
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
        return HttpResponseRedirect('/edit_mdt/{}'.format(mdt_id))


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
        return HttpResponseRedirect('/edit_mdt/{}'.format(mdt_id))


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

    variant_queryset = ProbandVariant.objects.filter(interpretation_report__in=report_list)

    mdt_form = MdtForm(instance=mdt_instance)

    if request.method == 'POST':
        mdt_form = MdtForm(request.POST, instance=mdt_instance)

        if mdt_form.is_valid():
            mdt_form.save()
            messages.add_message(request, 25, 'MDT Updated')

        return HttpResponseRedirect('/mdt_view/{}'.format(mdt_id))
    request.session['mdt_id'] = mdt_id
    return render(request, 'gel2mdt/mdt_view2.html', {'variant_queryset': variant_queryset,
                                                     'reports': reports,
                                                     'mdt_form': mdt_form,
                                                     'mdt_id': mdt_id})


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

            variant_queryset = ProbandVariant.objects.filter(interpretation_report__in=report_list)

            data['html_mdt_list'] = render_to_string('gel2mdt/includes/mdt_variant_table.html', {
                'variant_queryset': variant_queryset,
            })
        else:
            data['form_is_valid'] = False
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
            probands_in_mdt[mdt.id].append(report.interpretation_report.ir_family.participant_family.proband.gel_id)

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

