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
from gel2mdt.models import *
from gel2mdt.api.serializers import *

from django.http import Http404
from django.db.models import Prefetch

import pandas as pd

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

        qs = GELInterpretationReport.objects.filter(
            sample_type="raredisease"
        ).prefetch_related(
            *[
                'ir_family',
                'ir_family__participant_family__proband'
            ]
        )

        qs_df = pd.DataFrame(list(qs.values())).sort_values(
            by=[
                'ir_family_id',
                'archived_version'
            ]
        )
        multi_archived = qs_df.drop_duplicates(
            subset=['ir_family_id'],
            keep='last'
        )

        ids_of_latest = multi_archived["id"].tolist()
        queryset = GELInterpretationReport.objects.filter(
            id__in=ids_of_latest
        )

        return queryset

    serializer_class = GELInterpretationReportSerializer
