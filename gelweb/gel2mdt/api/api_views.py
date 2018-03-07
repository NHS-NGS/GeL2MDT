from gel2mdt.models import *
from django.contrib.auth.decorators import login_required
from rest_framework.decorators import api_view
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from gel2mdt.api.serializers import GELInterpretationReportSerializer


@api_view(['GET'])
def rare_disease_json(request):
    '''
    JSON response for all rare disease cases.
    '''
    all_gel_irs = GELInterpretationReport.objects.all()
    serializer = GELInterpretationReportSerializer(all_gel_irs, many=True)
    return Response(serializer.data)
