import os
import csv
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
    # target_variants = V
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
    # builds command from locations supplied in config file
    cmd = "{vep} --cache --dir_cache {cache} --fasta {fasta_loc} --hgvs --offline --symbol --sift b \
                   --polyphen b --fork 4 -q --no_stats -i temp.vcf -o temp.vep".format(
        vep=config_dict['vep'],
        cache=config_dict['cache'],
        fasta_loc=config_dict['fasta_loc'],
    )
    os.system(cmd)

def parse_vep_annotations():
    pass

def populate_transcript_table(vep):
    pass

def remove_temp_files():
    os.system("rm temp.vcf temp.vep")

# read in config file
config_dict = {}
with open("config.txt", 'r') as config_file:
    for line in config_file:
        line = line.strip().split('=', 1)
        config_dict[line[0]] = line[1]

variants = get_variants()
generate_vcf(variants)
run_vep()
remove_temp_files()