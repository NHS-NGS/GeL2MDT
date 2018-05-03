from .models import *
import django_filters


class ReportFilter(django_filters.FilterSet):

    class Meta:
        model = GELInterpretationReport
        fields = {'ir_family__ir_family_id': ['icontains',],
                  'ir_family__participant_family__proband__surname': ['icontains',],
                  'ir_family__participant_family__proband__forename': ['icontains',],
                  'ir_family__participant_family__proband__nhs_number': ['exact', ],
                  'ir_family__participant_family__proband__gel_id': ['exact', ],
                  'ir_family__participant_family__proband__lab_number': ['exact', ],
                  'ir_family__participant_family__proband__date_of_birth': ['exact', ],
                  'ir_family__participant_family__clinician__name': ['icontains', ],
                  }

    def __init__(self, *args, **kwargs):
        super(ReportFilter, self).__init__(*args, **kwargs)
        # at sturtup user doen't push Submit button, and QueryDict (in data) is empty
        if self.data == {}:
            self.queryset = self.queryset.none()