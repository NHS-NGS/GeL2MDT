from gel2mdt.models import *
from gel2mdt.api.serializers import *

from django.http import Http404
from django.db.models import Prefetch

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

    queryset = GELInterpretationReport.objects.all().prefetch_related(
        *[
            'ir_family',
            'ir_family__participant_family__proband',
        ]
    )
    serializer_class = GELInterpretationReportSerializer



class ProbandVariants(APIView):
    """
    Retrieve a set of proband variants for a given IR.
    """
    def get(self, request, pk, format=None):
        gel_ir = GELInterpretationReport.objects.get(id=pk)
        proband_variants = ProbandVariant.objects.filter(
            interpretation_report=gel_ir
        )

        serializer = ProbandVariantSerializer(proband_variants)
        return Response(serializer.data)


class ProbandDetail(generics.RetrieveUpdateAPIView):
    """
    Get information about a patient, or add/update a patient.
    """
    queryset = Proband.objects.all()
    serializer_class = ProbandSerializer





