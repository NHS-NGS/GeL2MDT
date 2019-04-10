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
from django.db import models
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import User, Group
import pandas as pd
from .api_utils.poll_api import PollAPI
from .model_utils.choices import ChoiceEnum
from .config import load_config


class ListUpdate(models.Model):
    """
    A table containing a single field which displays the each time the
    results list was updated.
    """
    update_time = models.DateTimeField()
    success = models.BooleanField()

    cases_added = models.IntegerField()
    cases_updated = models.IntegerField()
    reports_added = models.ManyToManyField('GELInterpretationReport', related_name='reports_added')
    reports_updated = models.ManyToManyField('GELInterpretationReport', related_name='reports_updated')
    sample_type = models.CharField(max_length=25, blank=True, null=True)
    error = models.TextField(null=True)

    class Meta:
        managed = True
        db_table = 'ListUpdate'
        app_label= 'gel2mdt'


class ToolOrAssemblyVersion(models.Model):
    """
    Represents a tool used or genome build and version used in several use cases
    within the CIP workflow.
    """
    class Meta:
        verbose_name_plural = "Tool and assembly versions"
        managed = True
        db_table = 'ToolOrAssemblyVersion'
        app_label= 'gel2mdt'

    tool_name = models.CharField(max_length=200)
    version_number = models.CharField(max_length=200)

    def __str__(self):
        return str(self.version_number)


class Phenotype(models.Model):
    description = models.CharField(max_length=200, null=True, blank=True)
    hpo_terms = models.CharField(max_length=200)

    def __str__(self):
        return str(self.description)

    class Meta:
        managed = True
        db_table = 'Phenotype'
        app_label= 'gel2mdt'


class Clinician(models.Model):
    name = models.CharField(max_length=200)
    hospital = models.CharField(max_length=200)
    email = models.EmailField()
    added_by_user = models.BooleanField(default=False)
    relates_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True)

    def __str__(self):
        return str(self.name)

    class Meta:
        managed = True
        db_table = 'Clinician'
        app_label= 'gel2mdt'


class Family(models.Model):
    """
    Represents a family within the CIP API: proband and relatives (if present)
    link to a particular family. Holds information about which panels have been
    applied to this case, which should be concordant with the phenotype of the
    proband.
    """
    class Meta:
        verbose_name_plural = "Families"
        db_table = 'Family'
        managed = True
        app_label= 'gel2mdt'
    gel_family_id = models.CharField(max_length=200, unique=True)

    clinician = models.ForeignKey(Clinician, on_delete=models.CASCADE)
    trio_sequenced = models.BooleanField()
    has_de_novo = models.BooleanField()

    def __str__(self):
        return str(self.gel_family_id)


class FamilyPhenotype(models.Model):
    """
    A linkage table for Family and Phenotype.
    """
    class Meta:
        managed = True
        db_table='FamilyPhenotype'
        app_label= 'gel2mdt'

    family = models.ForeignKey(Family, on_delete=models.CASCADE)
    phenotype = models.ForeignKey(Phenotype, on_delete=models.CASCADE)


class Gene(models.Model):
    """
    Represents an individual gene. Whilst HGNC names may change, use of the
    Ensembl ID hopes to be able to reference any gene consistently despite
    future name changes - the ENSG should not change.
    """
    ensembl_id = models.CharField(max_length=200)
    hgnc_name = models.CharField(max_length=200)
    hgnc_id = models.CharField(max_length=200, unique=True)
    description = models.CharField(max_length=200)

    def __str__(self):
        return str(self.hgnc_name)

    class Meta:
        managed = True
        db_table = 'Gene'
        app_label= 'gel2mdt'


class Panel(models.Model):
    """
    Represents a panel from panelApp which should be the panels used by GeL.
    Holds information about the relevant diseases.
    """
    panel_name = models.CharField(max_length=200)
    panelapp_id = models.CharField(max_length=200, unique=True)
    disease_group = models.CharField(max_length=200)
    disease_subgroup = models.CharField(max_length=200)

    def __str__(self):
        return str(self.panel_name)

    class Meta:
        managed = True
        db_table = 'Panel'
        app_label= 'gel2mdt'


class PanelVersion(models.Model):
    """
    Represents a version of a panel: holds a version number and list of
    genes for panel. Genes are listed here since they may change with each
    version.
    """
    panel = models.ForeignKey(Panel, on_delete=models.CASCADE)
    version_number = models.CharField(max_length=200)

    def __str__(self):
        return str(self.panel.panel_name + ' v' + self.version_number)

    class Meta:
        managed = True
        db_table = 'PanelVersion'
        app_label= 'gel2mdt'


class PanelVersionGene(models.Model):
    """
    Linkage table to relate Panels and Genes via a Many to Many relationship
    which is still compatible with the MultipleCaseAdder.
    """
    class Meta:
        managed = True
        app_label= 'gel2mdt'

    panel_version = models.ForeignKey(PanelVersion, on_delete=models.CASCADE)
    gene = models.ForeignKey(Gene, on_delete=models.CASCADE)

    level_of_confidence = models.CharField(max_length=200)


class InterpretationReportFamily(models.Model):
    """
    Acts as a container for all of the data for a particular report
    as it moves through the CIP workflow, allowing us to see how the
    data has changed as the status changes.
    """
    class Meta:
        verbose_name_plural = "Interpretation report families"
        managed = True
        db_table = 'InterpretationReportFamily'
        app_label= 'gel2mdt'

    ir_family_id = models.CharField(max_length=10, unique=True)
    participant_family = models.ForeignKey(
        Family, on_delete=models.CASCADE, null=True)

    priority = models.CharField(max_length=200)
    # some fields nullable to allow bulk saving before Panel and Family objects added

    # TODO: add choices once known. so far, I know of:
    # - omicia
    # - congenica
    # - nextcode
    # but there are probably more. need to be sure before choices added
    cip = models.CharField(max_length=200)

    # hash allows quicker determination of difference between reports
    # sha_hash = models.CharField(max_length=200)

    def __str__(self):
        return str(self.ir_family_id)


class InterpretationReportFamilyPanel(models.Model):
    """
    Linkages table to connect IRF with a Panel to allow M2M relationships
    that are still amenable to addition via the MCA.
    """
    class Meta:
        managed=True
        app_label= 'gel2mdt'

    ir_family = models.ForeignKey(InterpretationReportFamily, on_delete=models.CASCADE)
    panel = models.ForeignKey(PanelVersion, on_delete=models.CASCADE)

    custom = models.BooleanField(default=False)

    average_coverage = models.DecimalField(max_digits=6, decimal_places=2, null=True)
    proportion_above_15x = models.DecimalField(max_digits=6, decimal_places=5, null=True)

    genes_failing_coverage = models.TextField(null=True)


class GELInterpretationReportQuerySet(models.QuerySet):
    def latest_cases_by_sample_type(self, sample_type):
        qs = self.filter(sample_type=sample_type)
        if qs:
            # cases present
            qs_df = pd.DataFrame(list(qs.values())).sort_values(
                by=["ir_family_id", "archived_version"]
            )
            rm_dup_old = qs_df.drop_duplicates(
                subset=["ir_family_id"],
                keep="last"
            )
            ids_of_latest_cases = rm_dup_old["id"].tolist()
            return self.filter(id__in=ids_of_latest_cases)
        else:
            return qs

    def latest_cases_by_sample_type_and_user(self, sample_type, username):
        admin = False
        allowed_gmcs = []
        user = User.objects.get(username=username)
        for group in user.groups.all():
            if group.name == 'ADMIN GROUP':
                admin = True
            for gmc in group.grouppermissions.gmc.all():
                allowed_gmcs.append(gmc)
        qs = self.filter(sample_type=sample_type).prefetch_related('ir_family__participant_family__proband')
        if qs:
            # cases present
            qs_df = pd.DataFrame(list(qs.values())).sort_values(
                by=["ir_family_id", "archived_version"]
            )
            rm_dup_old = qs_df.drop_duplicates(
                subset=["ir_family_id"],
                keep="last"
            )
            ids_of_latest_cases = rm_dup_old["id"].tolist()
            if admin:
                return self.filter(id__in=ids_of_latest_cases)
            else:
                return self.filter(id__in=ids_of_latest_cases).filter(
                    ir_family__participant_family__proband__gmc__in=allowed_gmcs)
        else:
            return qs

    def latest_cases_by_user(self, username):
        qs = self.all()
        qs_df = pd.DataFrame(list(qs.values())).sort_values(
            by=["ir_family_id", "archived_version"]
        )
        rm_dup_old = qs_df.drop_duplicates(
            subset=["ir_family_id"],
            keep="last"
        )
        ids_of_latest_cases = rm_dup_old["id"].tolist()
        return self.filter(id__in=ids_of_latest_cases, assigned_user__username=username)


class GELInterpretationReport(models.Model):
    objects = GELInterpretationReportQuerySet.as_manager()

    ir_family = models.ForeignKey(
        InterpretationReportFamily, on_delete=models.CASCADE)
    archived_version = models.IntegerField(default=1)

    # TODO: add choices class for this based on spreadsheet
    status = models.CharField(max_length=200)
    updated = models.DateTimeField()

    sample_type = models.CharField(max_length=200, choices=(('cancer', 'cancer'),
                                                            ('raredisease', 'raredisease')))
    sample_id = models.CharField(max_length=200, null=True, blank=True)
    tumour_content = models.CharField(max_length=200, blank=True, null=True)
    has_germline_variant = models.BooleanField(default=False)

    max_tier = models.CharField(max_length=1, null=True)
    assembly = models.ForeignKey(ToolOrAssemblyVersion, on_delete=models.CASCADE)

    user = models.CharField(max_length=200)
    assigned_user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name='assigned_user')

    # sha hash to allow quick determination of differences each update
    sha_hash = models.CharField(max_length=200)
    polled_at_datetime = models.DateTimeField(default=timezone.now)

    case_sent = models.BooleanField(default=False)

    case_status = models.CharField(max_length=50, choices=(
        ('N', 'Not Started'), ('U', 'Under Review'), ('M', 'Awaiting MDT'), ('V', 'Awaiting Validation'),
        ('R', 'Awaiting Reporting'), ('P', 'Reported'), ('C', 'Completed'), ('E', 'External')), default='N')

    mdt_status = models.CharField(max_length=50, choices=(
        ('U', 'Unknown'),
        ('R', 'Required'), ('N', 'Not Required'), ('I', 'In Progress'), ('D', 'Done'),), default='U')
    pilot_case = models.BooleanField(default=False)
    no_primary_findings = models.BooleanField(default=False)
    case_code = models.CharField(max_length=20, null=True, blank=True, choices=(
        ('REANALYSE', 'REANALYSE'), ('URGENT', 'URGENT')), )
    first_check = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        default=None,
        related_name='first_check_user'
    )
    second_check = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        default=None,
        related_name='second_check_user'
    )

    def save(self, overwrite=False, *args, **kwargs):
        """
        Overwrite the model's save method to auto-increment versions for
        duplicate ir_familys. Pass in a InterpretationReportFamily entry.
        """
        archived_reports = GELInterpretationReport.objects.filter(
            ir_family=self.ir_family)
        if archived_reports:
            latest_report = archived_reports.latest('polled_at_datetime')
            if overwrite:
                latest_report.status = self.status
                latest_report.updated = self.updated
                latest_report.sample_type = self.sample_type
                latest_report.sample_id = self.sample_id
                latest_report.max_tier = self.max_tier
                latest_report.assembly = self.assembly
                latest_report.sha_hash = self.sha_hash
                latest_report.assigned_user = self.assigned_user
                latest_report.first_check = self.first_check
                latest_report.second_check = self.second_check
                latest_report.mdt_status = self.mdt_status
                latest_report.case_sent = self.case_sent
                latest_report.case_status = self.case_status
                latest_report.pilot_case = self.pilot_case
                latest_report.tumour_content = self.tumour_content
                latest_report.polled_at_datetime = timezone.now()
                latest_report.user = self.user
                latest_report.no_primary_findings = self.no_primary_findings
                latest_report.archived_version = self.archived_version
                latest_report.has_germline_variant = self.has_germline_variant
                latest_report.case_code = self.case_code
                super(GELInterpretationReport, latest_report).save(*args, **kwargs)
            else:
                self.assigned_user = latest_report.assigned_user
                self.first_check = latest_report.first_check
                self.second_check = latest_report.second_check
                self.mdt_status = latest_report.mdt_status
                self.case_sent = latest_report.case_sent
                self.case_status = latest_report.case_status
                self.pilot_case = latest_report.pilot_case
                self.polled_at_datetime = timezone.now()
                self.user = latest_report.user
                self.no_primary_findings = latest_report.no_primary_findings
                self.case_code = latest_report.case_code
                # update the latest saved version.
                self.archived_version = latest_report.archived_version + 1
                super(GELInterpretationReport, self).save(*args, **kwargs)
                mdt_report = MDTReport.objects.filter(interpretation_report=latest_report)
                if mdt_report:
                    for report in mdt_report:
                        report.interpretation_report = self
                        report.save()
                proband_variants = ProbandVariant.objects.filter(interpretation_report=latest_report)
                if proband_variants:
                    for pv in proband_variants:
                        pv.interpretation_report = self
                        pv.save()
                case_comments = CaseComment.objects.filter(interpretation_report=latest_report)
                if case_comments:
                    for comment in case_comments:
                        comment.interpretation_report = self
                        comment.save()

        else:
            self.archived_version = 1
            super(GELInterpretationReport, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.ir_family.ir_family_id + " v" + str(self.archived_version))

    class Meta:
        managed = True
        db_table = 'GELInterpretationReport'
        app_label= 'gel2mdt'


class ClinicalScientist(models.Model):
    name = models.CharField(max_length=200)
    hospital = models.CharField(max_length=200)
    email = models.EmailField()

    def __str__(self):
        return str(self.name)

    class Meta:
        managed = True
        db_table = 'ClinicalScientist'
        app_label = 'gel2mdt'


class Proband(models.Model):
    # these set to null to allow creation then updating later
    config_dict = load_config.LoadConfig().load()
    if config_dict['GMC'] != 'None':
        choices = config_dict['GMC'].split(',')
        gmc_choices = []
        for choice in choices:
            choice=choice.strip(' ')
            gmc_choices.append((choice, choice))

    gel_id = models.CharField(max_length=200, unique=True)
    family = models.OneToOneField(Family, on_delete=models.CASCADE)
    nhs_number = models.CharField(max_length=200, null=True, blank=True)
    # must be unique, but can also be null if not known
    lab_number = models.CharField(
        max_length=200, blank=True, null=True)
    forename = models.CharField(max_length=200)
    surname = models.CharField(max_length=200)
    date_of_birth = models.DateTimeField('date_of_birth')
    sex = models.CharField(max_length=10, null=True, blank=True)
    disease_group = models.CharField(max_length=200, null=True, blank=True)
    recruiting_disease = models.CharField(max_length=200, null=True, blank=True)
    disease_subtype = models.CharField(max_length=200, null=True, blank=True)
    disease_stage = models.CharField(max_length=200, null=True, blank=True)
    disease_grade = models.IntegerField(null=True, blank=True)
    previous_treatment = models.TextField(blank=True, null=True)
    currently_in_clinical_trial = models.BooleanField(default=False)
    current_clinical_trial_info = models.CharField(max_length=250, null=True, blank=True)
    suitable_for_clinical_trial = models.BooleanField(default=False)
    previous_testing = models.TextField(blank=True, null=True)
    outcome = models.TextField(blank=True)
    comment = models.TextField(blank=True)
    discussion = models.TextField(blank=True)
    action = models.TextField(blank=True)
    total_samples = models.IntegerField(null=True, blank=True)
    gmc = models.CharField(max_length=255, blank=True, default='Unknown')
    local_id = models.CharField(max_length=255, null=True, blank=True)

    deceased = models.NullBooleanField()

    def __str__(self):
        return str(self.gel_id)

    class Meta:
        managed = True
        db_table = 'Proband'
        app_label= 'gel2mdt'


class Relative(models.Model):
    gel_id = models.CharField(max_length=200)
    relation_to_proband = models.CharField(max_length=200)
    affected_status = models.CharField(max_length=200)
    proband = models.ForeignKey(Proband, on_delete=models.CASCADE)
    nhs_number = models.CharField(max_length=200, null=True)
    # must be unique, but can also be null if not known
    lab_number = models.CharField(
        max_length=200, blank=True, null=True)
    forename = models.CharField(max_length=200)
    surname = models.CharField(max_length=200)
    date_of_birth = models.DateTimeField('date_of_birth')
    sex = models.CharField(max_length=10, blank=True)

    sequenced = models.BooleanField()

    def __str__(self):
        return str(self.gel_id)

    class Meta:
        managed = True
        db_table = 'Relative'
        app_label= 'gel2mdt'


class Variant(models.Model):
    """
    Variant Info
    """
    chromosome = models.CharField(max_length=2)
    position = models.IntegerField()

    reference = models.TextField()
    alternate = models.TextField()

    db_snp_id = models.CharField(max_length=200, null=True)

    genome_assembly = models.ForeignKey(ToolOrAssemblyVersion, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.chromosome + str(self.position) + self.reference + ">" + self.alternate)

    class Meta:
        managed = True
        db_table = 'Variant'
        app_label= 'gel2mdt'


class Transcript(models.Model):
    name = models.CharField(max_length=255)
    canonical_transcript = models.BooleanField(default=False)
    strand = models.CharField(max_length=255)
    protein = models.CharField(max_length=255, null=True)
    location = models.CharField(max_length=255, null=True)

    gene = models.ForeignKey(Gene, on_delete=models.CASCADE, null=True)
    genome_assembly = models.ForeignKey(ToolOrAssemblyVersion, on_delete=models.CASCADE)

    def is_preferred_transcript(self):
        preferred_transcripts = PreferredTranscript.objects.filter(gene=self.gene,
                                                                   genome_assembly=self.genome_assembly,
                                                                   transcript=self)
        return preferred_transcripts.first()

    class Meta:
        managed = True
        db_table = 'Transcript'
        unique_together = (('name', 'genome_assembly'),)
        app_label= 'gel2mdt'


class PreferredTranscript(models.Model):
    transcript = models.ForeignKey(Transcript, on_delete=models.CASCADE)
    gene = models.ForeignKey(Gene, on_delete=models.CASCADE)
    genome_assembly = models.ForeignKey(ToolOrAssemblyVersion, on_delete=models.CASCADE)

    class Meta:
        managed = True
        db_table = 'PreferredTranscript'
        unique_together = (('gene', 'genome_assembly'),)
        app_label = 'gel2mdt'

        
class TranscriptVariant(models.Model):
    transcript = models.ForeignKey(Transcript, on_delete=models.CASCADE)
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)
    af_max = models.CharField(max_length=200)

    hgvs_c = models.TextField()
    hgvs_p = models.TextField()
    hgvs_g = models.TextField()

    sift = models.CharField(max_length=200, null=True)
    polyphen = models.CharField(max_length=200, null=True)
    pathogenicity = models.CharField(max_length=200, null=True)

    class Meta:
        managed = True
        db_table = 'TranscriptVariant'
        app_label= 'gel2mdt'


class Zygosities(ChoiceEnum):
    """
    A list of choices of zygosity that a variant can possibly have, used in the
    Variant model.
    """
    heterozygous = "heterozygous"
    reference_homozygous = "reference_homozygous"
    alternate_homozygous = "alternate_homozygous"
    unknown = "unknown"

class Inheritance(ChoiceEnum):
    """
    List of choices for whether a variant is inherited, de novo, or unknown.
    """
    unknown = "unknown"
    de_novo = "de_novo"
    inheritance = "inherited"


class ProbandVariant(models.Model):
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)
    max_tier = models.IntegerField(null=True)
    somatic = models.BooleanField()
    vaf = models.DecimalField(max_digits=8, decimal_places=3, null=True)

    interpretation_report = models.ForeignKey(
        GELInterpretationReport, on_delete=models.CASCADE)
    requires_validation = models.BooleanField(db_column='Requires_Validation', default=False)
    validation_status = models.CharField(max_length=50, choices=(
        ('U', 'Unknown'),
        ('A', 'Awaiting Validation'),
        ('K', 'Urgent Validation'),
        ('I', 'In Progress'),
        ('P', 'Passed Validation'),
        ('F', 'Failed Validation'),
        ('N', 'Not Required'),), default='U')
    validation_responsible_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        default=None
    )
    validation_datetime_set = models.DateTimeField(null=True, default=None)

    zygosity = models.CharField(
        # zygosity may also be 'unk' or 'missing', but this will default to
        # Zygosities.unknown
        max_length=20,
        choices=Zygosities.choices(),
        default=Zygosities.unknown)

    maternal_zygosity = models.CharField(
        max_length=20,
        choices=Zygosities.choices(),
        default=Zygosities.unknown)

    paternal_zygosity = models.CharField(
        max_length=20,
        choices=Zygosities.choices(),
        default=Zygosities.unknown)

    inheritance = models.CharField(
        max_length=20,
        choices=Inheritance.choices(),
        default=Inheritance.unknown)

    def __str__(self):
        return str(self.interpretation_report) + " " + str(self.variant)

    # Deselect the old transcript and select the provided one
    def select_transcript(self, selected_transcript):
        ProbandTranscriptVariant.objects.filter(proband_variant=self.id, selected=True).update(selected=False)
        ProbandTranscriptVariant.objects.filter(proband_variant=self.id,
                                                transcript=selected_transcript).update(selected=True)
        pvs = ProbandVariant.objects.filter(interpretation_report=self.interpretation_report)
        # Update the selected transcript for all PVs that have that transcript
        for pv in pvs:
            ptv_transcripts = ProbandTranscriptVariant.objects.filter(proband_variant=pv).values_list('transcript__name',
                                                                                                      flat=True)
            if selected_transcript.name in ptv_transcripts:
                ProbandTranscriptVariant.objects.filter(proband_variant=pv, selected=True).update(selected=False)
                ProbandTranscriptVariant.objects.filter(proband_variant=pv,
                                                        transcript=selected_transcript).update(selected=True)

    def get_transcript_variant(self):
        ptv = ProbandTranscriptVariant.objects.filter(selected=True, proband_variant=self.id)
        if len(ptv) == 1:
            transcript_variant = TranscriptVariant.objects.get(transcript=ptv[0].transcript,
                                                               variant=self.variant)
            return transcript_variant
        else:
            return None

    def get_transcript(self):
        ptv = ProbandTranscriptVariant.objects.filter(selected=True, proband_variant=self.id)
        if len(ptv) == 1:
            return ptv.first().transcript
        else:
            return None

    def get_preferred_transcript(self):
        ptvs = ProbandTranscriptVariant.objects.filter(proband_variant=self.id, selected=True)
        if len(ptvs) > 1 or len(ptvs) == 0:
            return None
        else:
            preferred_transcript = PreferredTranscript.objects.filter(genome_assembly=self.variant.genome_assembly,
                                                                      gene=ptvs.first().transcript.gene).first()
            return preferred_transcript

    def get_selected_count(self):
        ptv = ProbandTranscriptVariant.objects.filter(selected=True, proband_variant=self.id).count()
        return ptv

    def create_rare_disease_report(self):
        if not hasattr(self, 'rarediseasereport'):
            report = RareDiseaseReport(proband_variant=self)
            report.save()
            return report
        else:
            return self.rarediseasereport

    def create_cancer_report(self):
        if not hasattr(self, 'cancerreport'):
            report = CancerReport(proband_variant=self)
            report.save()
            return report
        else:
            return self.cancerreport

    class Meta:
        managed = True
        db_table = 'ProbandVariant'
        app_label= 'gel2mdt'


class PVFlag(models.Model):
    proband_variant = models.ForeignKey(ProbandVariant, on_delete=models.CASCADE)
    flag_name = models.CharField(db_column='flag_name', max_length=255)

    def __str__(self):
        return str(self.flag_name)

    class Meta:
        managed = True
        db_table = 'PVFlag'
        app_label = 'gel2mdt'


class RareDiseaseReport(models.Model):
    discussion = models.TextField(db_column='Discussion', blank=True, null=True)
    action = models.TextField(db_column='Action', blank=True, null=True)
    contribution_to_phenotype = models.CharField(db_column='Contribution_to_phenotype', max_length=20, choices=(
        ('NA', 'NA'),
        ('Uncertain', 'Uncertain'),
        ('None', 'None'),
        ('Full', 'Full'),
        ('Partial', 'Partial'),
        ('SE', 'Secondary'),
    ), default='NA')
    change_med = models.NullBooleanField(db_column='Change_med')
    surgical_option = models.NullBooleanField(db_column='Surgical_Option')
    add_surveillance_for_relatives = models.NullBooleanField(db_column='Add_surveillance_for_relatives')
    clinical_trial = models.NullBooleanField(db_column='Clinical_trial')
    inform_reproductive_choice = models.NullBooleanField(db_column='inform_reproductive_choice')
    classification = models.CharField(db_column='classification', max_length=2, choices=(
        ('NA', 'NA'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'), ('A', 'Artefact')
    ), default='NA')
    proband_variant = models.OneToOneField(ProbandVariant, on_delete=models.CASCADE, null=True)
    proband_sv = models.OneToOneField('ProbandSV', on_delete=models.CASCADE, null=True)
    proband_str = models.OneToOneField('ProbandSTR', on_delete=models.CASCADE, null=True)

    class Meta:
        managed = True
        db_table = 'RareDiseaseReport'
        app_label= 'gel2mdt'


class CancerReport(models.Model):
    action_choices = (('Predicts Therapeutic Response', 'Predicts Therapeutic Response'),
                      ('Prognostic', 'Prognostic'),
                      ('Defines diagnosis group', 'Defines diagnosis group'),
                      ('Eligibility for trial', 'Eligibility for trial'),
                      ('Other', 'Other'),)
    discussion = models.TextField(db_column='Discussion', blank=True)
    action = models.TextField(db_column='Action', blank=True)
    classification = models.CharField(db_column='classification', max_length=2, choices=(
        ('NA', 'NA'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'),
    ), default='NA')
    proband_variant = models.OneToOneField(ProbandVariant, on_delete=models.CASCADE)
    variant_use = models.CharField(max_length=200, null=True, blank=True)
    action_type = models.CharField(max_length=200, null=True, blank=True, choices=action_choices)
    validated = models.BooleanField(default=False)
    validated_assay_type = models.CharField(max_length=200, null=True, blank=True)

    class Meta:
        managed = True
        db_table = 'CancerReport'
        app_label= 'gel2mdt'


class ProbandTranscriptVariant(models.Model):
    transcript = models.ForeignKey(Transcript, on_delete=models.CASCADE)
    proband_variant = models.ForeignKey(ProbandVariant, on_delete=models.CASCADE)
    selected = models.BooleanField(default=False)
    effect = models.CharField(max_length=255)

    def get_transcript_variant(self):
        transcript_variant = TranscriptVariant.objects.get(transcript=self.transcript,
                                                           variant=self.proband_variant.variant)
        return transcript_variant

    class Meta:
        managed = True
        db_table = 'ProbandTranscriptVariant'
        app_label= 'gel2mdt'

# classes for choice
class ModesOfInheritance(ChoiceEnum):
    """
    A list of choices for modes of inheritance that each variant can possibly
    have. These are taken from the panelApp API, where they are an attribute
    of each gene. Used in the Variant model.
    """
    monoallelic_not_imprinted = "monoallelic_not_imprinted"
    monoallelic_maternally_imprinted = "monoallelic_maternally_imprinted"
    monoallelic_paternally_imprinted = "monoallelic_paternally_imprinted"
    monoallelic = "monoallelic"
    biallelic = "biallelic"
    monoallelic_and_biallelic = "monoallelic_and_biallelic"
    monoallelic_and_more_severe_biallelic = "monoallelic_and_more_severe_biallelic"
    xlinked_biallelic = "xlinked_biallelic"
    xlinked_monoallelic = "xlinked_monoallelic"
    mitochondrial = "mitochondrial"
    unknown = "unknown"


class ReportEvent(models.Model):
    """
    Represents a reported variant from the CIP. For each variant, there will
    likely be several report events, since the same gene is tested using different
    panels. This makes accessing key information harder for us but it's just the
    way that the CIP-API is set up.
    """
    re_id = models.CharField(max_length=200)
    tier = models.PositiveIntegerField(null=True)

    proband_variant = models.ForeignKey(ProbandVariant, on_delete=models.CASCADE, null=True) #made nullable
    panel = models.ForeignKey(PanelVersion, on_delete=models.CASCADE, null=True) #made nullable

    mode_of_inheritance = models.CharField(
        max_length=40,
        choices=ModesOfInheritance.choices(),
        default=ModesOfInheritance.unknown)
    penetrance = models.CharField(max_length=200)

    gene = models.ForeignKey(Gene, on_delete=models.CASCADE, null=True) #made nullable

    coverage = models.DecimalField(max_digits=8, decimal_places=3, null=True) #made nullable

    def __str__(self):
        return str(self.re_id)

    class Meta:
        managed = True
        db_table = 'ReportEvent'
        app_label= 'gel2mdt'


class Primer(models.Model):
    tool = models.ForeignKey(ToolOrAssemblyVersion, on_delete=models.CASCADE)
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)

    primer_set = models.CharField(max_length=200, unique=True)
    left_primer_seq = models.CharField(max_length=200)
    right_primer_seq = models.CharField(max_length=200)

    date_created = models.DateTimeField()

    def __str__(self):
        return str(self.primer_set)

    class Meta:
        managed = True
        db_table = 'Primer'
        app_label= 'gel2mdt'


class VariantReport(models.Model):
    proband_variant = models.OneToOneField(ProbandVariant, on_delete=models.CASCADE)

    primary_cs = models.ForeignKey(
        ClinicalScientist,
        related_name='primary_cs',
        on_delete=models.CASCADE)
    secondary_cs = models.ForeignKey(
        ClinicalScientist,
        related_name='secondary_cs',
        on_delete=models.CASCADE)

    classification = models.IntegerField(default=0)

    alamut_screenshot_splicesites = models.ImageField(
        upload_to="alamut_images/splicesites/%y/%m",
        null=True,
        blank=True)
    alamut_screenshot_sanger = models.ImageField(
        upload_to="alamut_images/splicesites/%y/%m",
        null=True,
        blank=True)

    # TODO: split this into multiple categorised fields
    comments = models.TextField()

    class Meta:
        managed = True
        db_table = 'VariantReport'
        app_label= 'gel2mdt'


class OtherStaff(models.Model):

    name = models.CharField(max_length=200)
    hospital = models.CharField(max_length=200)
    email = models.EmailField()


    class Meta:
        managed = True
        db_table = 'OtherStaff'
        app_label = 'gel2mdt'
        verbose_name_plural = "Other staff"


class MDT(models.Model):
    date_of_mdt = models.DateTimeField()
    sample_type = models.CharField(max_length=200, choices=(('cancer', 'cancer'),
                                                            ('raredisease', 'raredisease')))
    description = models.CharField(db_column='description', max_length=255, null=True, blank=True)
    # attending staff
    clinical_scientists = models.ManyToManyField(
        ClinicalScientist)
    clinicians = models.ManyToManyField(Clinician)
    other_staff = models.ManyToManyField(OtherStaff)

    # outcome: should the variant be reported?
    to_report = models.NullBooleanField()
    creator = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)  # Change to user foreignkey?
    status = models.CharField(db_column='Status', max_length=50, choices=(
        ('A', 'Active'), ('C', 'Completed')), default='A')
    gatb = models.NullBooleanField()
    sent_to_clinician = models.BooleanField(default=False)
    gtab_made = models.BooleanField(default=False)
    data_request_sent = models.BooleanField(default=False)
    gtab_sent = models.BooleanField(default=False)
    actions_sent = models.BooleanField(default=False)

    def __str__(self):
        return str(self.date_of_mdt)

    class Meta:
        managed = True
        db_table = 'MDT'
        app_label= 'gel2mdt'


class MDTReport(models.Model):
    interpretation_report = models.ForeignKey(GELInterpretationReport, on_delete=models.CASCADE)
    MDT = models.ForeignKey(MDT, on_delete=models.CASCADE)

    class Meta:
        managed = True
        db_table = 'MDTReport'
        app_label = 'gel2mdt'


class CaseAlert(models.Model):
    gel_id = models.CharField(max_length=30)
    comment = models.CharField(max_length=255)
    sample_type = models.CharField(max_length=20, choices=(('cancer', 'cancer'),
                                                           ('raredisease', 'raredisease')))

    class Meta:
        managed = True
        db_table = 'GELAlert'
        app_label = 'gel2mdt'


class CaseComment(models.Model):
    interpretation_report = models.ForeignKey(GELInterpretationReport, on_delete=models.CASCADE)
    comment = models.TextField()
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    time = models.DateTimeField()

    class Meta:
        managed = True
        ordering = ['-time']
        db_table = 'CaseComment'
        app_label = 'gel2mdt'


class SVRegion(models.Model):
    chromosome = models.CharField(max_length=5)
    sv_start = models.IntegerField()
    sv_end = models.IntegerField()
    genome_assembly = models.ForeignKey(ToolOrAssemblyVersion, on_delete=models.PROTECT)

    class Meta:
        managed = True
        unique_together = (('chromosome', 'sv_start', 'sv_end', 'genome_assembly'),)
        db_table = 'SVRegion'
        app_label = 'gel2mdt'

    def liftover_grch(self):
        if self.genome_assembly.version_number == 'GRCh38':
            genome = 'GRCh37'
        elif self.genome_assembly.version_number == 'GRCh37':
            genome = 'GRCh38'
        request_list_poll = PollAPI(
            "ensembl",
            f"map/human/{self.genome_assembly}/{self.chromosome}:{self.sv_start}..{self.sv_end}:1/{genome}?"
        )
        try:
            request_list_poll.get_json_response()
            result_json = request_list_poll.response_json["mappings"][0]["mapped"]
            return f"{result_json['seq_region_name']}:{result_json['start']}-{result_json['end']}"
        except:
            return None


class SV(models.Model):
    sv_region1 = models.ForeignKey(SVRegion, on_delete=models.CASCADE, related_name='region1')
    sv_region2 = models.ForeignKey(SVRegion, on_delete=models.CASCADE, null=True, related_name='region2')
    variant_type = models.CharField(max_length=40, choices=(('i', 'insertion'),
                                                            ('p', 'duplication'),
                                                            ('v', 'inversion'),
                                                            ('a', 'amplification'),
                                                            ('d', 'deletion'),
                                                            ('t', 'tandem_duplication'),
                                                            ('dm', 'deletion_mobile_element'),
                                                            ('im', 'insertion_mobile_element'),))

    def __str__(self):
        return f"{self.sv_region1.chromosome}:{self.sv_region1.sv_start}-{self.sv_region1.sv_end}"

    class Meta:
        managed = True
        unique_together = (('sv_region1', 'sv_region2', 'variant_type'),)
        db_table = 'SV'
        app_label = 'gel2mdt'


class ProbandSV(models.Model):
    """
    Proband structural variants
    """

    interpretation_report = models.ForeignKey('GELInterpretationReport', on_delete=models.CASCADE)
    sv = models.ForeignKey(SV, on_delete=models.CASCADE)
    VALIDATION_CHOICES = (('U', 'Unknown'),
                            ('A', 'Awaiting Validation'),
                            ('K', 'Urgent Validation'),
                            ('I', 'In Progress'),
                            ('P', 'Passed Validation'),
                            ('F', 'Failed Validation'),
                            ('N', 'Not Required'),)
    validation_status = models.CharField(choices=VALIDATION_CHOICES, max_length=4, default='U')
    validation_datetime_set = models.DateTimeField(null=True, default=None)
    validation_responsible_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        default=None
    )
    max_tier = models.CharField(max_length=20, null=True)
    cnv_af = models.FloatField(null=True)
    cnv_auc = models.FloatField(null=True)

    def create_rare_disease_report(self):
        if not hasattr(self, 'rarediseasereport'):
            report = RareDiseaseReport(proband_sv=self)
            report.save()
            return report
        else:
            return self.rarediseasereport

    class Meta:
        managed = True
        unique_together = (('sv', 'interpretation_report',),)
        db_table = 'ProbandSV'
        app_label = 'gel2mdt'


class ProbandSVGene(models.Model):
    """
    Selected gene for a Proband
    """
    proband_sv = models.ForeignKey('ProbandSV', on_delete=models.CASCADE)
    gene = models.ForeignKey('Gene', on_delete=models.CASCADE)
    selected = models.BooleanField(default=False)

    class Meta:
        managed = True
        unique_together = (('proband_sv', 'gene',),)
        db_table = 'ProbandSVGene'
        app_label = 'gel2mdt'


class STRVariant(models.Model):
    """
    Short tandem repeat variants
    """
    chromosome = models.CharField(max_length=5)
    str_start = models.IntegerField()
    str_end = models.IntegerField()
    genome_assembly = models.ForeignKey(ToolOrAssemblyVersion, on_delete=models.PROTECT)
    repeated_sequence = models.CharField(max_length=32)
    normal_threshold = models.IntegerField()
    pathogenic_threshold = models.IntegerField()

    def __str__(self):
        return f"{self.chromosome}:{self.str_start}-{self.str_end}"

    class Meta:
        managed = True
        unique_together = (('chromosome', 'str_start', 'str_end', 'genome_assembly', 
            'repeated_sequence', 'normal_threshold', 'pathogenic_threshold'),)
        db_table = 'STRVariant'
        app_label = 'gel2mdt'


class ProbandSTR(models.Model):
    """
    Proband short tandem repeat variants
    """
    interpretation_report = models.ForeignKey('GELInterpretationReport', on_delete=models.CASCADE)
    str_variant = models.ForeignKey(STRVariant, on_delete=models.CASCADE)
    max_tier = models.CharField(max_length=20, null=True)
    proband_copies_a = models.IntegerField(null=True)
    proband_copies_b = models.IntegerField(null=True)
    maternal_copies_a = models.IntegerField(null=True)
    maternal_copies_b = models.IntegerField(null=True)
    paternal_copies_a = models.IntegerField(null=True)
    paternal_copies_b = models.IntegerField(null=True)
    mode_of_inheritance = models.CharField(max_length=128, null=True)
    segregation_pattern = models.CharField(max_length=128, null=True)
    requires_validation = models.BooleanField(db_column='Requires_Validation', default=False)
    validation_status = models.CharField(max_length=50, choices=(
        ('U', 'Unknown'),
        ('A', 'Awaiting Validation'),
        ('K', 'Urgent Validation'),
        ('I', 'In Progress'),
        ('P', 'Passed Validation'),
        ('F', 'Failed Validation'),
        ('N', 'Not Required'),), default='U')
    validation_responsible_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        default=None
    )
    validation_datetime_set = models.DateTimeField(null=True, default=None)

    def __str__(self):
        for gene in self.probandstrgene_set.all():
            if gene.selected:
                return gene.gene.hgnc_name

    def create_rare_disease_report(self):
        if not hasattr(self, 'rarediseasereport'):
            report = RareDiseaseReport(proband_str=self)
            report.save()
            return report
        else:
            return self.rarediseasereport


    class Meta:
        managed = True
        unique_together = (('str_variant', 'interpretation_report',),)
        db_table = 'ProbandSTR'
        app_label = 'gel2mdt'


class ProbandSTRGene(models.Model):
    """
    Selected gene for a Proband
    """
    proband_str = models.ForeignKey('ProbandSTR', on_delete=models.CASCADE)
    gene = models.ForeignKey('Gene', on_delete=models.CASCADE)
    selected = models.BooleanField(default=False)

    class Meta:
        managed = True
        unique_together = (('proband_str', 'gene',),)
        db_table = 'ProbandSTRGene'
        app_label = 'gel2mdt'


class GMC(models.Model):
    name = models.CharField(max_length=255)

    class Meta:
        managed = True
        db_table = 'GMC'
        app_label = 'gel2mdt'

    def __str__(self):
        return str(self.name)


class GroupPermissions(models.Model):
    gmc = models.ManyToManyField(GMC)
    group = models.OneToOneField(Group, on_delete=models.CASCADE)
    cancer = models.BooleanField(default=False, help_text="Indicates whether the group can view Cancer Cases")
    raredisease = models.BooleanField(default=False, help_text="Indicates whether the group can view Rare Disease Cases")

    can_view_pvs = models.BooleanField(default=False, help_text="Indicates whether the group can view Proband Variants ")
    can_view_svs = models.BooleanField(default=False, help_text="Indicates whether the group can view Proband Structural Variants ")
    can_view_strs = models.BooleanField(default=False, help_text="Indicates whether the group can view Proband STRs")

    can_select_update_transcript = models.BooleanField(default=False, help_text="Indicates whether the group can update transcripts and select preferred Transcripts")
    pull_t3_variants = models.BooleanField(default=False, help_text="Indicates whether the group can Pull T3 Variants")
    can_edit_proband = models.BooleanField(default=False, help_text="Indicates whether the group can edit proband Information")
    can_edit_completed_proband = models.BooleanField(default=False,
                                                     help_text="Indicates whether the group can view & edit a Completed Proband")
    can_edit_gelir = models.BooleanField(default=False, help_text="Indicates whether the group can edit Case information")
    can_edit_mdt = models.BooleanField(default=False, help_text="Indicates whether the group can edit MDT questions")
    can_get_gel_report = models.BooleanField(default=False, help_text="Indicates whether the group can pull the GEL report")
    can_edit_relative = models.BooleanField(default=False, help_text="Indicates whether the group can edit relative information")
    can_edit_clinical_questions = models.BooleanField(default=False, help_text="Indicates whether the group can edit cancer clinical questions")
    start_mdt = models.BooleanField(default=False, help_text="Indicates whether the group can start MDTs")
    can_edit_case_alert = models.BooleanField(default=False, help_text="Indicates whether the group can view & edit Case Alerts")
    can_edit_validation_list = models.BooleanField(default=False, help_text="Indicates whether the group can view & edit the validation list")

    def __str__(self):
        return str(self.group.name)

    class Meta:
        managed = True
        db_table = 'GroupPermissions'
        app_label = 'gel2mdt'
