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
from rest_framework import serializers
from gel2mdt.models import *


class ProbandSerializer(serializers.ModelSerializer):
    """
    Serialiser for returning Proband detail JSONs through the REST framework.
    """
    class Meta:
        """
        Meta class for ProbandSerializer, which defines the model and fields.

        Attributes:
            model (gel2mdt.models.Proband): class def for Proband model
            fields (tuple): tuple of strings related to Proband model attrs
        """
        model = Proband
        fields = (
            'gel_id',
            'nhs_number',
            'lab_number',
            'forename',
            'surname',
            'date_of_birth',
            'local_id',
        )


class ProbandVariantSerializer(serializers.ModelSerializer):
    """
    Serialiser for returning ProbandVariant detail JSONs via REST framework.

    Because not all desired fields come from the ProbandVariant model itself,
    the defined attributes are required to set a source for a human-readable
    represenation of the serialised field.

    Attributes:
        variant (serializers.CharField): defines source of string repr of the
            genomic position of the variant.
        interpretation (serializers.CharField): defines source of string repr
            of the interpretation request as an ID of format XXXX-X.
        gene (serializers.CharField): defines source of string repr of the gene
            associated with the particular ProbandVariant - typically HGNC name.
        transcript (serializers.CharField): defines source of string repr of the
            transcript as ENSTID based on a ProbandVariant's get_transcript
            class method.
        hgvs_c (serializers.CharField): defines source of string repr of the
            HGVSc for a particular ProbandVariant, which comes from the
            associated Variant via ProbandVariant's get_transcript_variant class
            method.
        hgvs_p (serializers.CharField): defines source of string repr of the
            HGVSp for a particular ProbandVariant, which comes from the
            associated Variant via ProbandVariant's get_transcript_variant class
            method.
    """
    variant = serializers.CharField(
        source="variant.id",
        read_only=True)
    interpretation = serializers.CharField(
        source="rare_disease_report.id",
        read_only=True)
    gene = serializers.CharField(
        source="get_transcript.gene",
        read_only=True)
    transcript = serializers.CharField(
        source="get_transcript.name",
        read_only=True)
    hgvs_c = serializers.CharField(
        source="get_transcript_variant.hgvs_c",
        read_only=True)
    hgvs_p = serializers.CharField(
        source="get_transcript_variant.hgvs_p",
        read_only=True)


    class Meta:
        """
        Meta class for ProbandSerializer, which defines the model and fields.

        Attributes:
            model (gel2mdt.models.ProbandVariant): class def for ProbandVariant
                model
            fields (tuple): tuple of strings related to ProbandVariant model
                attrs
        """
        model = ProbandVariant
        fields = (
            "variant",
            "interpretation",
            "gene",
            "transcript",
            "hgvs_c",
            "hgvs_p",
            "zygosity",
            "inheritance"
        )


class GELInterpretationReportSerializer(serializers.ModelSerializer):
    """
    Serialiser for returning GEL IR detail JSONs via REST framework.

    This serialiser feeds the /api/gelir/raredisease and /api/gelir/cancer
    endpoints.

    Because not all desired fields come from the GELInterpretationReport model
    itself, the defined attributes are required to set a source for a
    human-readable  represenation of the serialised field.

    Attributes:
        ir_family (serializers.CharField): define source of GeL family ID as
            string repr as e.g. 2100XXXXX code.
        assembly (serializers.CharField): define source of genome build as
            string repr (GRCh37 or GRCh38).
        gel_id (serializers.CharField): define source of GeL proband ID as
             string repr as e.g. 2100XXXXX code; typically the same as ir_family
             code.
        cip_id (serializers.CharField): define source of GEL IR ID as string
            repr in form XXXX-X
        gmc (serializers.CharField): define source of string repr for case's
            genomic medicine centre code (e.g. RRK for Birmingham).
        clinician (serializers.CharField): define source of string repr for
            case's related clinician, given as name in string format.
        forename (serializers.CharField): define source of string repr of cases'
            patient forename.
        surname (serializers.CharField): define source of string repr of cases'
            patient surname.
        date_of_birth (serializers.DateTimeField): define source of DT repr of
            cases' patient date of birth.
        cip_status (serializers.CharField): define source of string repr of
            the CIP API status of the case.
        case_status (serializers.CharField): define source of string repr of
            the status of the case, as manually set by users.
        trio_sequenced (serializer.BooleanField): define source of bool repr of
            whether (T) or not (F) a case has a proband, mother, and father
            sequenced.
        has_de_novo (serializer.BooleanField): defines source of bool repr of
            whether (T) or not (F) a case has ProbandVariants which are de novo.
        case_type (serializer.CharField): defines source of str repr of the
            case type, either <str:raredisease> or <str:cancer>.
        updated (serializer.DateTimeField): defines source of DT repr of
            when the JSON was last changed in the CIP-API.
        assigned_user (serializer.StringRelatedField): defines source of
            the user account assigned to this case, given as <str:username>

    """
    ir_family = serializers.CharField(
        source="ir_family.ir_family_id",
        read_only=True
    )
    assembly = serializers.StringRelatedField()

    gel_id = serializers.CharField(
        source="ir_family.participant_family.proband.gel_id",
        read_only=True
    )
    nhs_num = serializers.CharField(
        source="ir_family.participant_family.proband.nhs_number",
        read_only=True
    )
    disease_subtype = serializers.CharField(
        source="ir_family.participant_family.proband.disease_subtype",
        read_only=True
    )
    sex = serializers.CharField(
        source="ir_family.participant_family.proband.sex",
        read_only=True
    )
    cip_id = serializers.CharField(
        source="ir_family.ir_family_id",
        read_only=True
    )
    gmc = serializers.CharField(
        source="ir_family.participant_family.proband.gmc",
        read_only=True
    )
    clinician = serializers.CharField(
        source="ir_family.participant_family.clinician",
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
    nhs_number = serializers.CharField(
        source="ir_family.participant_family.proband.nhs_number",
        read_only=True
    )
    date_of_birth = serializers.DateTimeField(
        source="ir_family.participant_family.proband.date_of_birth",
        read_only=True,
        format='%Y/%m/%d'
    )

    trio_sequenced = serializers.CharField(
        source="ir_family.participant_family.trio_sequenced",
        read_only=True
    )

    has_de_novo = serializers.BooleanField(
        source="ir_family.participant_family.has_de_novo",
        read_only=True
    )

    cip_status = serializers.CharField(
        source="status",
        read_only=True
    )

    case_status = serializers.CharField(
        source="get_case_status_display",
        read_only=True
    )
    mdt_status = serializers.CharField(
        source="get_mdt_status_display",
        read_only=True
    )
    updated = serializers.DateTimeField(
        format='%Y/%m/%d',
        read_only=True
    )
    priority = serializers.CharField(
        source='ir_family.priority',
        read_only=True
    )
    recruiting_disease = serializers.CharField(
        source="ir_family.participant_family.proband.recruiting_disease",
        read_only=True
    )

    assigned_user = serializers.StringRelatedField()


    class Meta:
        """
        Meta for GELInterpretationReportSerializer, defines the model and fields.

        Attributes:
            model (gel2mdt.models.GELInterpretationReport): class def for
                GELInterpretationReport model
            fields (tuple): tuple of strings related to ProbandVariant model
                attrs
        """
        model = GELInterpretationReport
        fields = (
            'id',
            'gel_id',
            'cip_id',
            'gmc',
            'clinician',
            'forename',
            'surname',
            'nhs_number',
            'date_of_birth',
            'case_status',
            'trio_sequenced',
            'has_de_novo',
            'has_germline_variant',
            'pilot_case',
            'ir_family',
            'archived_version',
            'status',
            'updated',
            'sample_type',
            'max_tier',
            'assembly',
            'user',
            'assigned_user',
            'priority',
            'recruiting_disease',
            'sex',
            'nhs_num',
            'disease_subtype',
            'case_code',
            'cip_status',
            'mdt_status'
        )
