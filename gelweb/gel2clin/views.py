from django.shortcuts import render
from django.shortcuts import render, redirect
from . import *
from gel2mdt.models import *
from gel2mdt.config import load_config
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    return render(request, 'gel2clin/index.html', {'sample_type': None})


@login_required
def cancer_main(request):
    '''
    Shows all the Cancer cases the user has access to and allows easy searching of cases
    :param request:
    :return:
    '''
    return render(request, 'gel2clin/cancer_main.html', {'sample_type': 'cancer'})


@login_required
def rare_disease_main(request):
    '''
    Shows all the RD cases the user has access to and allows easy searching of cases
    :param request:
    :return:
    '''
    return render(request, 'gel2clin/rare_disease_main.html', {'sample_type': 'raredisease'})


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
    proband_variants = ProbandVariant.objects.filter(interpretation_report=report)
    proband_mdt = MDTReport.objects.filter(interpretation_report=report)
    panels = InterpretationReportFamilyPanel.objects.filter(ir_family=report.ir_family)

    return render(request, 'gel2clin/proband.html', {'report': report,
                                                    'relatives': relatives,
                                                    'proband_variants': proband_variants,
                                                    'proband_mdt': proband_mdt,
                                                    'panels': panels,
                                                    'sample_type': report.sample_type})
