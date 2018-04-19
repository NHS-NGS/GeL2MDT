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
    List all rare disease cases in our database, filtered by <str:sample_type>.

    Sample type may be "raredisease" or "cancer" to return the associated cases.
    Inherits from rest_framework.generics.ListAPIView, which displays a list of
    all serialised model fields as defined by the GELInterpretationReportSerializer.

    Attributes:
        serializer_class (rest_framework.serializers.ModelSerializer): serialiser
            which processes the queryset given by class method get_queryset(),
            then used to generate the JSON response for the API view.
    """

    def get_queryset(self):
        """
        Return a queryset of GELInterpretationReport instances based upon the
        kwarg 'sample_type' used to initialise the class.

        Returns:
            queryset (django.query.QuerySet): queryset used to initialise the
                serializer_class from GELInterpretationReportSerializer
        """
        sample_type = self.kwargs['sample_type']
        queryset = GELInterpretationReport.objects.filter(sample_type=sample_type).prefetch_related(
            *[
                'ir_family',
                'ir_family__participant_family__proband',
            ]
        )
        return queryset
    serializer_class = GELInterpretationReportSerializer

