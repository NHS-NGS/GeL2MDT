from rest_framework import serializers
from gel2mdt.models import GELInterpretationReport


class GELInterpretationReportSerializer(serializers.ModelSerializer):

    # fetch the IR family in a readable form
    ir_family = serializers.CharField(
        source="ir_family.ir_family_id",
        read_only=True
    )
    assembly = serializers.StringRelatedField()


    class Meta:
        model = GELInterpretationReport
        fields = (
            'ir_family',
            'archived_version',
            'status',
            'updated',
            'sample_type',
            'max_tier',
            'assembly',
            'user'
        )
