import os
import csv
from ..config import load_config
from . import parse_vep
#from ..config import load_config
#from gel2mdt.models import *

class TargetVariant:
    def __init__(self, chromosome, position, variant_id, ref, alt):
        self.chromosome = chromosome
        self.position = position
        self.variant_id = variant_id
        self.ref = ref
        self.alt = alt

class TargetTranscript:
    def __init__(self, gene_ensembl_id, strand, hgvs_c, hgvs_p):
        self.gene_ensembl_id = gene_ensembl_id
        self.strand = strand
        self.hgvs_c = hgvs_c
        self.hgvs_p = hgvs_p

def get_variants():
    target_variants = []
    # TODO: for variants not linked to transcript, create variant object and add to list
    # target_variants = Variants
    # temp solution makes 3 target variants for testing purposes:
    tv1 = TargetVariant(20, 14370, "id-001", "G", "A")
    tv2 = TargetVariant(20, 17330, "id-002", "T", "A")
    tv3 = TargetVariant(22, 51135978, "id-003", "A", "C")
    target_variants = [tv1,tv2,tv3]
    return target_variants


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
    annotated_vartiants_dict = parse_vep.ParseVep().read_file('temp.vep.vcf')
    print(annotated_vartiants_dict)
    # TODO: create variant and transript objects to then be added into the models

def populate_transcript_table(vep):
    pass

def remove_temp_files():
    os.system("rm temp.vcf temp.vep")

def genetate_transcipts():
    variants = get_variants()
    generate_vcf(variants)
    run_vep()
    parse_vep_annotations()
    #remove_temp_files()
