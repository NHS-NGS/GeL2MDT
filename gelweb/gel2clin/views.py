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
from django.shortcuts import render
from django.shortcuts import render, redirect
from . import *
from gel2mdt.models import *
from gel2mdt.config import load_config
from django.contrib.auth.decorators import login_required
from .forms import ProbandCancerForm
from django.contrib import messages


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

    if request.method=='POST':
        form = ProbandCancerForm(request.POST, instance=report.ir_family.participant_family.proband)
        form.save()
        messages.add_message(request, 25, 'Clinical History Updated')
    if report.sample_type == 'cancer':
        form = ProbandCancerForm(instance=report.ir_family.participant_family.proband)
        return render(request, 'gel2clin/cancer_proband.html', {'report': report,
                                                                     'relatives': relatives,
                                                                     'proband_variants': proband_variants,
                                                                     'proband_mdt': proband_mdt,
                                                                     'panels': panels,
                                                                     'sample_type': report.sample_type,
                                                                     'form': form})
    else:
        return render(request, 'gel2clin/raredisease_proband.html', {'report': report,
                                                    'relatives': relatives,
                                                    'proband_variants': proband_variants,
                                                    'proband_mdt': proband_mdt,
                                                    'panels': panels,
                                                    'sample_type': report.sample_type})
