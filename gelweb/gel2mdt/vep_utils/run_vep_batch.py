import os
import csv
from ..config import load_config
from . import parse_vep

class CaseVariant:
    def __init__(self, chromosome, position, case_id, ref, alt):
        print("Creating case variant!")
        self.chromosome = chromosome
        self.position = position
        self.variant_id = case_id
        self.ref = ref
        self.alt = alt

class CaseTranscript:
    def __init__(self, gene_ensembl_id, gene_hgnc_name, transcript_name, transcript_canonical, transcript_strand,
                 proband_transcript_variant_effect, proband_variant_af_max, variant_polyphen, variant_sift,
                 transcript_variant_hgvs_c, transcript_variant_hgvs_p):
        self.gene_ensembl_id = gene_ensembl_id
        self.gene_hgnc_name = gene_hgnc_name
        self.transcript_name = transcript_name
        self.transcript_canonical = transcript_canonical
        self.transcript_strand = transcript_strand
        self.proband_transcript_variant_effect = proband_transcript_variant_effect
        self.proband_variant_af_max = proband_variant_af_max
        self.variant_polyphen = variant_polyphen
        self.variant_sift = variant_sift
        self.transcript_variant_hgvs_c = transcript_variant_hgvs_c
        self.transcript_variant_hgvs_p = transcript_variant_hgvs_p

# def get_variants():
#     target_variants = []
#     # TODO: for variants not linked to transcript, create variant object and add to list
#     # target_variants = Variants
#     # temp solution makes 3 target variants for testing purposes:
#     tv1 = CaseVariant(20, 14370, "id-001", "G", "A")
#     tv2 = CaseVariant(20, 17330, "id-002", "T", "A")
#     tv3 = CaseVariant(22, 51135978, "id-003", "A", "C")
#     target_variants = [tv1,tv2,tv3]
#     return target_variants


def generate_vcf(variants):
    with open('temp.vcf', 'w') as vcffile:
        f = csv.writer(vcffile, delimiter='\t')
        for variant in variants:
            f.writerow([variant.chromosome, variant.position, variant.variant_id, variant.ref, variant.alt])

def run_vep():
    config_dict = load_config.LoadConfig().load()
    # builds command from locations supplied in config file
    cmd = "{vep} -i temp.vcf -o temp.vep.vcf --cache --dir_cache {cache} --fork 4 --vcf --flag_pick \
            --exclude_predicted --everything --dont_skip --total_length --offline --fasta {fasta_loc}".format(
        vep=config_dict['vep'],
        cache=config_dict['cache'],
        fasta_loc=config_dict['fasta_loc'],
    )
    os.system(cmd)

def parse_vep_annotations():
    variants = parse_vep.ParseVep().read_file('temp.vep.vcf')
    transcripts_list = []
    for variant in variants:
        for transcript in variant['transcript_data']:
            gene_id = variant['transcript_data'][transcript]['Gene']
            gene_name = variant['transcript_data'][transcript]['SYMBOL']
            if variant['transcript_data'][transcript]['CANONICAL'] == '':
                canonical = False
            else:
                canonical = variant['transcript_data'][transcript]['CANONICAL']
            transcript_name = variant['transcript_data'][transcript]['Feature']
            transcript_strand = variant['transcript_data'][transcript]['STRAND']
            proband_transcript_variant_effect = variant['transcript_data'][transcript]['Consequence']
            proband_variant_af_max = variant['transcript_data'][transcript]['MAX_AF']
            variant_polyphen = variant['transcript_data'][transcript]['PolyPhen']
            variant_sift = variant['transcript_data'][transcript]['SIFT']
            transcript_variant_hgvs_c = variant['transcript_data'][transcript]['HGVSc']
            transcript_variant_hgvs_p = variant['transcript_data'][transcript]['HGVSp']
            case_transcript = CaseTranscript(gene_id, gene_name, transcript_name, canonical, transcript_strand,
                                             proband_transcript_variant_effect, proband_variant_af_max,
                                             variant_polyphen, variant_sift, transcript_variant_hgvs_c,
                                             transcript_variant_hgvs_p)
            transcripts_list.append(case_transcript)
    return transcripts_list

# def populate_transcript_table(vep):
#     pass

def remove_temp_files():
    os.system("rm temp.vcf temp.vep.vcf")

def generate_transcripts(variant_list):
    #variant_list = get_variants()
    generate_vcf(variant_list)
    run_vep()
    transcript_list = parse_vep_annotations()
    remove_temp_files()
    return transcript_list

