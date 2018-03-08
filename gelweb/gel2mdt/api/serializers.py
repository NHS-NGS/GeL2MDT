from rest_framework import serializers
from gel2mdt.models import *


class GELInterpretationReportSerializer(serializers.ModelSerializer):

    # fetch the IR family in a readable form
    ir_family = serializers.CharField(
        source="ir_family.ir_family_id",
        read_only=True
    )
    assembly = serializers.StringRelatedField()

    # get proband information
    proband_id = serializers.CharField(
        source="ir_family.participant_family.proband.id",
        read_only=True
    )
    gel_id = serializers.CharField(
        source="ir_family.participant_family.proband.gel_id",
        read_only=True
    )
    forename = serializers.CharField(
        source="ir_family.participant_family.proband.forename",
        read_only=True
    )
    surname = serializers.CharField(
        source="ir_family.participant_family.proband.surname",
        read_only=True
    )
    date_of_birth = serializers.DateTimeField(
        source="ir_family.participant_family.proband.date_of_birth",
        read_only=True,
        format='%Y/%m/%d'
    )
    case_status = serializers.CharField(
        source="ir_family.participant_family.proband.get_status_display",
        read_only=True
    )

    updated = serializers.DateTimeField(
        format='%Y/%m/%d',
        read_only=True
    )


    class Meta:
        model = GELInterpretationReport
        fields = (
            'proband_id',
            'gel_id',
            'forename',
            'surname',
            'date_of_birth',
            'case_status',
            'ir_family',
            'archived_version',
            'status',
            'updated',
            'sample_type',
            'max_tier',
            'assembly',
            'user'
        )
