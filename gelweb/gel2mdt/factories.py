import datetime
import factory
import random

from . import models

from django.contrib.auth.models import User


class ClinicianFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Clinician

    name = factory.Faker('last_name', locale='en-GB')
    email = 'unknown'
    hospital = factory.Faker('lexify', text='???', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ')


class OtherStaffFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.OtherStaff

    name = factory.Faker('last_name', locale='en-GB')
    email = 'unknown'
    hospital = factory.Faker('lexify', text='???', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ')


class ClinicianScientistFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ClinicalScientist

    name = factory.Faker('last_name', locale='en-GB')
    email = 'unknown'
    hospital = factory.Faker('lexify', text='???', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ')


class PhenotypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Phenotype

    description = factory.Faker('sentence')
    hpo_terms = factory.Faker('numerify', text='HP:#######')


class ProbandFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Proband

    gel_id = factory.Faker('numerify', text='#########')
    family = factory.SubFactory(FamilyFactory)
    nhs_number = factory.Faker('numerify', text='##########')

    lab_number = factory.Faker('numerify', text='D########')
    local_id = factory.Faker('numerify', text='#######')
    forename = factory.Faker('first_name', locale='en-GB')
    surname = factory.Faker('last_name', locale='en-GB')

    date_of_birth = factory.Faker(
        'date_time_between',
        start_date='-75y',
        end_date='-3y')
    sex = factory.Faker('random_element', elements=('Male','Female'))

    pilot_case = factory.Faker('boolean', chance_of_getting_true=85)

    gmc = factory.Faker('lexify', text='???', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ')

    status = 'Not Started'
    mdt_status = 'Required'


class FamilyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Family

    gel_family_id = factory.Faker('numerify', text='#########')
    clinician = factory.SubFactory(ClinicianFactory)
    proband = factory.SubFactory(ProbandFactory)


class FamilyPhenotypeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.FamilyPhenotype

    family = factory.SubFactory(FamilyFactory)
    phenotype = factory.SubFactory(PhenotypeFactory)


class PanelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Panel

    panel_name = factory.Faker('sentence')
    panelapp_id = factory.Faker('md5')
    disease_group = factory.Faker('sentence', nb_words=1)
    disease_subgroup = factory.Faker('sentence', nb_words=1)

class PanelVersionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PanelVersion

    panel = factory.SubFactory(PanelFactory)
    version_number = factory.Faker('numerify', text='#.##')


class GeneFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Gene

    ensembl_id = factory.Faker('numerify', text='ENSG00000######')
    hgnc_name = factory.Faker('bothify', text='????#', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    hgnc_id = factory.Faker('numerify', text='#####')
    description = factory.Faker('sentence')

class PanelVersionGene(factory.django.DjangoModelFactory):
    class Meta:
        model = models.PanelVersionGene

    panel_version = factory.SubFactory(PanelVersionFactory)
    gene = factory.SubFactory(GeneFactory)

    level_of_confidence = factory.Faker('random_element', elements=(
        # duplication of High because these are most prominent
        'HighEvidence',
        'HighEvidence',
        'HighEvidence',
        'ModerateEvidence',
        'ModerateEvidence',
        'LowEvidence'
    ))


class ToolOrAssemblyVersionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ToolOrAssemblyVersion

    tool_name = factory.Faker('job')
    version_number = factory.Faker('numerify', text='#.##')


class GenomeBuildFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ToolOrAssemblyVersion

    tool_name = 'genome build'
    version_number = factory.Faker('random_element', elements=('GRCh37','GRCh38'))

class TranscriptFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Transcript

    name = factory.Faker('numerify', text='ENST00000######')
    # default is False, need to set 1 to be True when creating
    canonical_transcript = False
    strand = factory.Faker('random_element', elements=('1','-1'))

    protein = factory.Faker('bothify', text='????#', letters='ABCDEFGHIJKLMNOPQRSTUVWXYZ')
    location = factory.Faker('numerify', text='########')

    gene = factory.SubFactory(GeneFactory)
    genome_assembly = factory.SubFactory(GenomeBuildFactory)




class RelativeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Relative

    gel_id = factory.Faker('numerify', text='#########')
    relation_to_proband = factory.Faker('random_element', elements=(
        'Mother',
        'Father',
        'FullSibling'
    ))
    affected_status = factory.Faker('random_element', elements=(
        'Affected',
        'Not affected'
    ))
    proband = factory.SubFactory(ProbandFactory)
    nhs_number = factory.Faker('numerify', text='##########')

    lab_number = factory.Faker('numerify', text='D########')
    forename = factory.Faker('first_name', locale='en-GB')
    surname = factory.Faker('last_name', locale='en-GB')

    date_of_birth = factory.Faker(
        'date_time_between',
        start_date='-75y',
        end_date='-3y')
    sex = factory.Faker('random_element', elements=('Male','Female'))


class InterpretationReportFamilyFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.InterpretationReportFamily

    ir_family_id = factory.Faker('numerify', text='####-1')
    participant_family = factory.SubFactory(FamilyFactory)

    priority = factory.Faker('random_element', elements=('High', 'Low'))
    cip = factory.Faker('random_element', elements=('Sapientia', 'Omicia', 'NextCode', 'WuXi'))


class InterpretationReportFamilyPanelFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.InterpretationReportFamilyPanel

    panel = factory.SubFactory(PanelVersionFactory)
    ir_family = factory.SubFactory(InterpretationReportFamilyFactory)


class GELInterpretationReportFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.GELInterpretationReport

    ir_family = factory.SubFactory(InterpretationReportFamilyFactory)
    status = factory.Faker('random_element', elements=(
        'sent_to_gmcs',
        'report_generated',
        'report_sent'
    ))

    updated = factory.Faker('past_date', start_date='-30d')
    sample_type = 'raredisease'

    user = factory.Faker('last_name')
    sha_hash = factory.Faker('sha256')
    polled_at_datetime = datetime.datetime.now()


class VariantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Variant

    chromosome = factory.Faker('random_element', elements=(
        '1','2','3','4','5','6','7','8','9','10','11','12','13','14','15','16','17','18','19','20','21','22','23','X','Y','MT','M')
    )
    position = random.randint(0,32000000000)

    reference = factory.Faker('lexify', text='?', letters='ATCG')
    alternate = factory.Faker('lexify', text='?', letters='ATCG')

    db_snp_id = factory.Faker('numerify', text='rs##########')

    genome_assembly = factory.SubFactory(GenomeBuildFactory)


class ProbandVariantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ProbandVariant

    variant = factory.SubFactory(VariantFactory)
    max_tier = random.randint(0,3)
    somatic = False

    interpretation_report = factory.SubFactory(GELInterpretationReportFactory)
    zygosity = factory.Faker('random_element', elements=(
        'heterozygous',
        'reference_homozygous',
        'alternate_homozygous',
        'unknown'
    ))


class TranscriptVariantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.TranscriptVariant

    transcript = factory.SubFactory(TranscriptFactory)
    variant = factory.SubFactory(VariantFactory)

    af_max = factory.Faker('numerify', text='0.##')

    hgvs_c = factory.Faker('bothify', text='ENST00000######?>?', letters='ACTG')
    hgvs_p = factory.Faker('bothify', text='ENSP00000######?>?', letters='GALMFWKQESPVICYHRNDT')
    hgvs_g = factory.Faker('bothify', text='#:#########?>?', letters='ACTG')


class ProbandTranscriptVariantFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ProbandTranscriptVariant

    proband_variant = factory.SubFactory(ProbandVariantFactory)
    transcript = factory.SubFactory(TranscriptFactory)

    selected = False
    effect = factory.Faker('random_element', elements=(
        'transcript_ablation',
        'splice_acceptor_variant',
        'splice_donor_variant',
        'stop_gained',
        'frameshift_variant',
        'stop_lost',
        'start_lost',
        'transcript_amplification',
        'inframe_insertion',
        'inframe_deletion',
        'missense_variant',
        'protein_altering_variant',
        'splice_region_variant',
        'incomplete_terminal_codon_variant',
        'stop_retained_variant',
        'synonymous_variant',
        'coding_sequence_variant',
        'mature_miRNA_variant',
        '5_prime_UTR_variant',
        '3_prime_UTR_variant',
        'non_coding_transcript_exon_variant',
        'intron_variant',
        'NMD_transcript_variant',
        'non_coding_transcript_variant',
        'upstream_gene_variant',
        'downstream_gene_variant',
        'TFBS_ablation',
        'TFBS_amplification',
        'TF_binding_site_variant',
        'regulatory_region_ablation',
        'regulatory_region_amplification',
        'feature_elongation',
        'regulatory_region_variant',
        'feature_truncation',
        'intergenic_variant',
    ))


class ReportEventFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ReportEvent

    re_id = factory.Faker('numerify', text='RE###')
    tier = random.randint(1,3)

    proband_variant = factory.SubFactory(ProbandVariantFactory)
    panel = factory.SubFactory(PanelVersionFactory)

    mode_of_inheritance = factory.Faker('random_element', elements = (
        'monoallelic_not_imprinted',
        'monoallelic_maternally_imprinted',
        'monoallelic_paternally_imprinted',
        'monoallelic',
        'biallelic',
        'monoallelic_and_biallelic',
        'monoallelic_and_more_severe_biallelic',
        'xlinked_biallelic',
        'xlinked_monoallelic',
        'mitochondrial',
        'unknown'
    ))

    penetrance = factory.Faker('random_element', elements = (
        'complete',
        'incomplete'
    ))

    coverage = random.randint(0,1500)


class ListUpdateFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.ListUpdate

    update_time = factory.Faker('past_date', start_date='-30d')

    success = True

    cases_added = random.randint(0,15)
    cases_updated = random.randint(0,15)

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User

    username = factory.Faker('first_name')


class MDTFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.MDT

    date_of_mdt = factory.Faker('past_date', start_date='-30d')
    creator = factory.SubFactory(UserFactory)


class RareDiseaseReportFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.RareDiseaseReport


class MDTReportFactoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.MDTReport

    interpretation_report = factory.SubFactory(GELInterpretationReportFactory)
    mdt = factory.SubFactory(MDTFactory)


class PrimerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = models.Primer

    tool = factory.SubFactory(ToolOrAssemblyVersionFactory)
    variant = factory.SubFactory(VariantFactory)

    primer_set = factory.Faker('md5')

    left_primer_seq = factory.Faker('lexify', text='?????????????????????', letters='ATCG')
    right_primer_seq = factory.Faker('lexify', text='?????????????????????', letters='ATCG')

