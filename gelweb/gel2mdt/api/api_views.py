from gel2mdt.models import *
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from gel2mdt.api.serializers import GELInterpretationReportSerializer


@login_required
def rare_disease_json(request):
    '''
    JSON response for all rare disease cases.
    '''
    all_gel_irs = GELInterpretationReport.objects.all()
    serializer = GELInterpretationReportSerializer(all_gel_irs, many=True)
    return JsonResponse(serializer.data, safe=False)
