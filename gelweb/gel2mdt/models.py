from django.db import models
from django.utils import timezone

from .model_utils.choices import ChoiceEnum


class ListUpdate(models.Model):
    """
    A table containing a single field which displays the each time the
    results list was updated.
    """
    update_time = models.DateTimeField()
    success = models.BooleanField()

    cases_added = models.IntegerField()
    cases_updated = models.IntegerField()

    error = models.TextField(null=True)


class ToolOrAssemblyVersion(models.Model):
    """
    Represents a tool used or genome build and version used in several use cases
    within the CIP workflow.
    """
    class Meta:
        verbose_name_plural = "Tool and assembly versions"
        managed = True
        db_table = 'ToolOrAssemblyVersion'

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


class Clinician(models.Model):
    name = models.CharField(max_length=200)
    hospital = models.CharField(max_length=200)
    email = models.EmailField()

    def __str__(self):
        return str(self.name)

    class Meta:
        managed = True
        db_table = 'Clinician'


class Family(models.Model):
    """
    Represents a family within the CIP API: proband and relatives (if present)
    link to a particular family. Holds information about which panels have been
o   applied to this case, which should be concordant with the phenotype of the
    proband.
    """
    class Meta:
        verbose_name_plural = "Families"
        db_table = 'Family'
        managed = True
    gel_family_id = models.CharField(max_length=200, unique=True)

    clinician = models.ForeignKey(Clinician, on_delete=models.CASCADE)

    def __str__(self):
        return str(self.gel_family_id)


class FamilyPhenotype(models.Model):
    """
    A linkage table for Family and Phenotype.
    """
    class Meta:
        managed = True
        db_table='FamilyPhenotype'

    family = models.ForeignKey(Family, on_delete=models.CASCADE)
    phenotype = models.ForeignKey(Phenotype, on_delete=models.CASCADE)


class Gene(models.Model):
    """
    Represents an individual gene. Whilst HGNC names may change, use of the
    Ensembl ID hopes to be able to reference any gene consistently despite
    future name changes - the ENSG should not change.
    """
    ensembl_id = models.CharField(max_length=200, unique=True)
    hgnc_name = models.CharField(max_length=200)

    description = models.CharField(max_length=200)

    def __str__(self):
        return str(self.hgnc_name)

    class Meta:
        managed = True
        db_table = 'Gene'


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


class PanelVersionGene(models.Model):
    """
    Linkage table to relate Panels and Genes via a Many to Many relationship
    which is still compatible with the MultipleCaseAdder.
    """
    class Meta:
        managed = True

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

    ir_family = models.ForeignKey(InterpretationReportFamily, on_delete=models.CASCADE)


class GELInterpretationReport(models.Model):
    ir_family = models.ForeignKey(
        InterpretationReportFamily, on_delete=models.CASCADE)
    archived_version = models.IntegerField(default=1)

    # TODO: add choices class for this based on spreadsheet
    status = models.CharField(max_length=200)
    updated = models.DateTimeField()

    sample_type = models.CharField(max_length=200, choices=(('cancer', 'cancer'),
                                                            ('raredisease', 'raredisease')))

    def max_tier(self):
        """
        Get all PV associated with this variant and then return min or most
        significant tier of all of these.
        """
        proband_variant_tiers = ProbandVariant.objects.filter(
            interpretation_report=self
        ).values_list('max_tier', flat=True)
        try:
            return min(proband_variant_tiers)
        except ValueError as e:
            return 3

    def assembly(self):
        """
        Look at the variants and return the assemblies.
        """
        proband_variants = ProbandVariant.objects.filter(
            interpretation_report=self
        )
        proband_variant_assemblies = []
        for pv in proband_variants:
            proband_variant_assemblies.append(pv.variant.genome_assembly)
        proband_variant_assemblies = set(proband_variant_assemblies)
        proband_variant_assemblies = list(proband_variant_assemblies)

        if len(proband_variant_assemblies) == 1:
            return proband_variant_assemblies[0]
        else:
            return proband_variant_assemblies

    # would be nice if this could link to the clinical scientist table
    # but wel also have "gel" and CIPs as users.
    user = models.CharField(max_length=200)

    # sha hash to allow quick determination of differences each update
    sha_hash = models.CharField(max_length=200)
    polled_at_datetime = models.DateTimeField(default=timezone.now)

    def get_max_tier(self):
        variants = Variant.objects.filter(interpretation_report=self)
        tiers = variants.value_list('tier', flat=True)
        return min(tiers)

    def save(self, *args, **kwargs):
        """
        Overwrite the model's save method to auto-increment versions for
        duplicate ir_familys. Pass in a InterpretationReportFamily entry.
        """
        archived_reports = GELInterpretationReport.objects.filter(
            ir_family=self.ir_family)
        if archived_reports.exists():
            latest_report = archived_reports.latest('polled_at_datetime')
            self.archived_version = latest_report.archived_version + 1
        else:
            self.archived_version = 1

        super(GELInterpretationReport, self).save(*args, **kwargs)

    def __str__(self):
        return str(self.ir_family.ir_family_id + " v" + str(self.archived_version))

    class Meta:
        managed = True
        db_table = 'GELInterpretationReport'


class ClinicalScientist(models.Model):
    name = models.CharField(max_length=200)
    hospital = models.CharField(max_length=200)
    email = models.EmailField()

    def __str__(self):
        return str(self.name)

    class Meta:
        managed = True
        db_table = 'ClinicalScientist'


class Proband(models.Model):
    # these set to null to allow creation then updating later
    gel_id = models.CharField(max_length=200, unique=True)
    family = models.OneToOneField(Family, on_delete=models.CASCADE)
    nhs_number = models.CharField(max_length=200, null=True)
    # must be unique, but can also be null if not known
    lab_number = models.CharField(
        max_length=200, unique=True, blank=True, null=True)
    forename = models.CharField(max_length=200)
    surname = models.CharField(max_length=200)
    date_of_birth = models.DateTimeField('date_of_birth')
    sex = models.CharField(max_length=10, blank=True)
    pilot_case = models.BooleanField(default=False)
    outcome = models.TextField(blank=True)
    comment = models.TextField(blank=True)
    discussion = models.TextField(blank=True)
    action = models.TextField(blank=True)
    episode = models.CharField( max_length=255, blank=True)
    gmc = models.CharField( max_length=255)
    local_id = models.CharField(max_length=255)
    case_sent = models.BooleanField(default=False)
    status = models.CharField( max_length=50, choices=(
        ('N', 'Not Started'), ('U', 'Under Review'), ('M', 'Awaiting MDT'), ('V', 'Awaiting Validation'),
        ('R', 'Awaiting Reporting'), ('P', 'Reported'), ('C', 'Completed'), ('E', 'External')), default='N')

    mdt_status = models.CharField( max_length=50, choices=(
        ('R', 'Required'), ('N', 'Not Required'), ('I', 'In Progress'), ('D', 'Done'),), default='R')
    deceased = models.NullBooleanField()

    def __str__(self):
        return str(self.gel_id)

    class Meta:
        managed = True
        db_table = 'Proband'


class Relative(models.Model):
    gel_id = models.CharField(max_length=200, unique=True)
    relation_to_proband = models.CharField(max_length=200)
    affected_status = models.CharField(max_length=200)
    proband = models.ForeignKey(Proband, on_delete=models.CASCADE)
    nhs_number = models.CharField(max_length=200, null=True)
    # must be unique, but can also be null if not known
    lab_number = models.CharField(
        max_length=200, unique=True, blank=True, null=True)
    forename = models.CharField(max_length=200)
    surname = models.CharField(max_length=200)
    date_of_birth = models.DateTimeField('date_of_birth')
    sex = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return str(self.gel_id)

    class Meta:
        managed = True
        db_table = 'Relative'


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


class Transcript(models.Model):
    name = models.CharField(max_length=255, unique=True)
    canonical_transcript = models.BooleanField(default=False)
    strand = models.CharField(max_length=255)
    protein = models.CharField(max_length=255, null=True)
    location = models.CharField(max_length=255, null=True)

    class Meta:
        managed = True
        db_table = 'Transcript'


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


class Zygosities(ChoiceEnum):
    """
    A list of choices of zygosity that a variant can possibly have, used in the
    Variant model.
    """
    heterozygous = "heterozygous"
    reference_homozygous = "reference_homozygous"
    alternate_homozygous = "alternate_homozygous"
    unknown = "unknown"

class ProbandVariant(models.Model):
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)
    max_tier = models.IntegerField()
    somatic = models.BooleanField()
    vaf = models.DecimalField(max_digits=8, decimal_places=3, null=True)

    interpretation_report = models.ForeignKey(
        GELInterpretationReport, on_delete=models.CASCADE)

    zygosity = models.CharField(
        max_length=20,
        choices=Zygosities.choices(),
        default=Zygosities.unknown)

    # TODO: find where to get these from


    def __str__(self):
        return str(self.interpretation_report) + " " + str(self.variant)

    # Deselect the old transcript and select the provided one
    def select_transcript(self, selected_transcript):
        ProbandTranscriptVariant.objects.filter(proband_variant=self.id, selected=True).update(selected=False)
        ProbandTranscriptVariant.objects.filter(proband_variant=self.id,
                                                transcript=selected_transcript).update(selected=True)

    def create_rare_disease_report(self):
        if not hasattr(self, 'rarediseasereport'):
            report = RareDiseaseReport(proband_variant=self)
            report.save()

    class Meta:
        managed = True
        db_table = 'ProbandVariant'


class RareDiseaseReport(models.Model):
    discussion = models.TextField(db_column='Discussion', blank=True)
    action = models.TextField(db_column='Action', blank=True)
    contribution_to_phenotype = models.CharField(db_column='Contribution_to_phenotype', max_length=2, choices=(
        ('UN', 'Uncertain'), ('No', 'None'), ('FU', 'Full'), ('PA', 'Partial'), ('SE', 'Secondary'), ('NA', 'NA')
    ), default='NA')
    change_med = models.NullBooleanField(db_column='Change_med')
    surgical_option = models.NullBooleanField(db_column='Surgical_Option')
    add_surveillance_for_relatives = models.NullBooleanField(db_column='Add_surveillance_for_relatives')
    clinical_trial = models.NullBooleanField(db_column='Clinical_trial')
    inform_reproductive_choice = models.NullBooleanField(db_column='inform_reproductive_choice')
    classification = models.CharField(db_column='classification', max_length=2, choices=(
        ('NA', 'NA'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'),
    ), default='NA')
    proband_variant = models.OneToOneField(ProbandVariant, on_delete=models.CASCADE)

    class Meta:
        managed = True
        db_table = 'RareDiseaseReport'


class CancerReport(models.Model):
    discussion = models.TextField(db_column='Discussion', blank=True)
    action = models.TextField(db_column='Action', blank=True)
    classification = models.CharField(db_column='classification', max_length=2, choices=(
        ('NA', 'NA'), ('1', '1'), ('2', '2'), ('3', '3'), ('4', '4'), ('5', '5'),
    ), default='NA')
    proband_variant = models.OneToOneField(ProbandVariant, on_delete=models.CASCADE)

    class Meta:
        managed = True
        db_table = 'CancerReport'




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

    def __str__(self):
        pass

    class Meta:
        managed = True
        db_table = 'VariantReport'


class OtherStaff(models.Model):
    class Meta:
        verbose_name_plural = "Other staff"

    name = models.CharField(max_length=200)
    hospital = models.CharField(max_length=200)
    email = models.EmailField()

    def __str__(self):
        pass

    class Meta:
        managed = True
        db_table = 'OtherStaff'


class MDT(models.Model):
    date_of_mdt = models.DateTimeField()

    # attending staff
    clinical_scientists = models.ManyToManyField(
        ClinicalScientist)
    clinicians = models.ManyToManyField(Clinician)
    other_staff = models.ManyToManyField(OtherStaff)

    # outcome: should the variant be reported?
    to_report = models.NullBooleanField()
    creator = models.CharField(db_column='Creator', max_length=255)  # Change to user foreignkey?
    status = models.CharField(db_column='Status', max_length=50, choices=(
        ('A', 'Active'), ('C', 'Completed')), default='A')
    gatb = models.NullBooleanField()

    def __str__(self):
        return str(self.date_of_mdt)

    class Meta:
        managed = True
        db_table = 'MDT'

class MDTReport(models.Model):
    interpretation_report = models.ForeignKey(GELInterpretationReport, on_delete=models.CASCADE)
    MDT = models.ForeignKey(MDT, on_delete=models.CASCADE)

    class Meta:
        managed = True
        db_table = 'MDTReport'

