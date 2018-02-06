from django.db import models
from django.utils import timezone

from .model_utils.choices import ChoiceEnum


class ListUpdate(models.Model):
    """
    A table containing a single field which displays the each time the
    results list was updated.
    """
    update_time = models.DateTimeField()


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
    gel_family_id = models.IntegerField(unique=True)

    clinician = models.ForeignKey(Clinician, on_delete=models.CASCADE)
    phenotypes = models.ManyToManyField(Phenotype)

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
    ensembl_id = models.CharField(max_length=200, unique=True, null=True)
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

    genes = models.ManyToManyField(Gene)

    def __str__(self):
        return str(self.panel.panel_name + ' v' + self.version_number)

    class Meta:
        managed = True
        db_table = 'PanelVersion'


class ToolOrAssembly(models.Model):
    """
    Represents a tool used or genome build used in several use cases within the
    CIP workflow. Provides a link to the tool's webpage.
    """
    class Meta:
        verbose_name_plural = "Tools and assemblies"
        managed = True
        db_table = 'ToolOrAssembly'

    tool_name = models.CharField(max_length=200, unique=True)
    reference_link = models.URLField(max_length=200)

    def __str__(self):
        return str(self.tool_name)


class ToolOrAssemblyVersion(models.Model):
    """
    Represents a version of a tool or assembly: holds a version number.
    """
    class Meta:
        verbose_name_plural = "Tool and assembly versions"
        managed = True
        db_table = 'ToolOrAssemblyVersion'

    tool = models.ForeignKey(ToolOrAssembly, on_delete=models.CASCADE)
    version_number = models.CharField(max_length=200)

    def __str__(self):
        return str(self.tool.tool_name + ' v' + self.version_number)


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
    panels = models.ManyToManyField(PanelVersion)
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


class GELInterpretationReport(models.Model):
    ir_family = models.ForeignKey(
        InterpretationReportFamily, on_delete=models.CASCADE)
    archived_version = models.IntegerField(default=1)

    # TODO: add choices class for this based on spreadsheet
    status = models.CharField(max_length=200)
    updated = models.DateTimeField()

    # would be nice if this could link to the clinical scientist table
    # but wel also have "gel" and CIPs as users.
    user = models.CharField(max_length=200)

    # sha hash to allow quick determination of differences each update
    sha_hash = models.CharField(max_length=200)
    polled_at_datetime = models.DateTimeField(default=timezone.now)

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
    gel_id = models.IntegerField(unique=True)
    family = models.OneToOneField(Family, on_delete=models.CASCADE)
    nhs_number = models.CharField(max_length=200, null=True) # removed unique contraint as labkey down
    # must be unique, but can also be null if not known
    lab_number = models.CharField(
        max_length=200, unique=True, blank=True, null=True)
    forename = models.CharField(max_length=200)
    surname = models.CharField(max_length=200)
    date_of_birth = models.DateTimeField('date_of_birth')
    sex = models.CharField(max_length=10, blank=True)
    pilot_case = models.NullBooleanField()
    outcome = models.TextField(blank=True)
    comment = models.TextField(blank=True)
    discussion = models.TextField(blank=True)
    action = models.TextField(blank=True)
    episode = models.CharField( max_length=255, blank=True)
    gmc = models.CharField( max_length=255)
    local_id = models.CharField(max_length=255)
    case_sent = models.NullBooleanField()
    status = models.CharField( max_length=50, choices=(
        ('N', 'Not Started'), ('U', 'Under Review'), ('M', 'Awaiting MDT'), ('V', 'Awaiting Validation'),
        ('R', 'Awaiting Reporting'), ('P', 'Reported'), ('C', 'Completed'), ('E', 'External')), default='N')

    mdt_status = models.CharField( max_length=50, choices=(
        ('R', 'Required'), ('N', 'Not Required'), ('I', 'In Progress'), ('D', 'Done'),), default='R')

    def __str__(self):
        return str(self.gel_id)

    class Meta:
        managed = True
        db_table = 'Proband'


class Relative(models.Model):
    gel_id = models.IntegerField(unique=True)
    relation_to_proband = models.CharField(max_length=200)
    affected_status = models.CharField(max_length=200)
    proband = models.ForeignKey(Proband, on_delete=models.CASCADE)
    nhs_number = models.CharField(max_length=200, null=True) # removed unique contraint as labkey down
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
    hgvs_g = models.CharField(max_length=255, unique=True, null=True)

    reference = models.CharField(max_length=200)
    alternate = models.CharField(max_length=200)

    db_snp_id = models.CharField(max_length=200)

    genome_assembly = models.CharField(max_length=200)

    def __str__(self):
        return str(self.chromosome + str(self.position) + self.reference + ">" + self.alternate)

    class Meta:
        managed = True
        db_table = 'Variant'
        unique_together = (('chromosome', 'position', 'reference', 'alternate'),)


class Transcript(models.Model):
    name = models.CharField(max_length=255)
    canonical_transcript = models.CharField(max_length=255)
    strand = models.CharField(max_length=255)
    protein = models.CharField(max_length=255, null=True)
    location = models.CharField(max_length=255, null=True)

    gene = models.ForeignKey(Gene, on_delete=models.CASCADE, null=True)

    class Meta:
        managed = True
        db_table = 'Transcript'


class TranscriptVariant(models.Model):
    transcript = models.ForeignKey(Transcript, on_delete=models.CASCADE)
    variant = models.ForeignKey(Variant, on_delete=models.CASCADE)
    af_max = models.CharField(max_length=200)

    hgvs_c = models.CharField(max_length=255)
    hgvs_p = models.CharField(max_length=255)

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

    interpretation_report = models.ForeignKey(
        GELInterpretationReport, on_delete=models.CASCADE)

    zygosity = models.CharField(
        max_length=20,
        choices=Zygosities.choices(),
        default=Zygosities.unknown)

    # TODO: find where to get these from

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

    def __str__(self):
        return str(self.interpretation_report) + " " + str(self.variant)

    class Meta:
        managed = True
        db_table = 'ProbandVariant'


class ProbandTranscriptVariant(models.Model):
    transcipt = models.OneToOneField(Transcript, on_delete=models.CASCADE)
    proband_variant = models.OneToOneField(ProbandVariant, on_delete=models.CASCADE)

    effect = models.CharField(max_length=255)

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
    tier = models.PositiveIntegerField()

    proband_variant = models.ForeignKey(ProbandVariant, on_delete=models.CASCADE, null=True) #made nullable
    panel = models.ForeignKey(PanelVersion, on_delete=models.CASCADE, null=True) #made nullable

    mode_of_inheritance = models.CharField(
        max_length=40,
        choices=ModesOfInheritance.choices(),
        default=ModesOfInheritance.unknown)
    penetrance = models.CharField(max_length=200)

    gene = models.ForeignKey(Gene, on_delete=models.CASCADE, null=True) #made nullable
    phenotype = models.ForeignKey(Phenotype, on_delete=models.CASCADE, null=True) #made nullable

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

