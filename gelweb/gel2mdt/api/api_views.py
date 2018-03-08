from gel2mdt.models import *
from gel2mdt.api.serializers import *

from django.http import Http404
from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework import mixins
from rest_framework import generics


class RareDiseaseCases(generics.ListAPIView):
    """
    List all rare disease cases in our database.
    """
    queryset = GELInterpretationReport.objects.all()
    serializer_class = GELInterpretationReportSerializer


class ProbandDetail(generics.RetrieveUpdateAPIView):
    """
    Get information about a patient, or add/update a patient.
    """
    queryset = Proband.objects.all()
    serializer_class = ProbandSerializer





