import os
import tempfile
import subprocess
import csv
from ..config import load_config
from . import parse_vep

class CaseVariant:
    def __init__(self, chromosome, position, case_id, variant_count, ref, alt):
        print("Creating case variant!")
        self.chromosome = chromosome
        self.position = position
        self.case_id = case_id
        self.variant_count = variant_count
        self.ref = ref
        self.alt = alt

class CaseTranscript:
    def __init__(self, case_id, variant_count, gene_ensembl_id, gene_hgnc_name, transcript_name, transcript_canonical,
                 transcript_strand, proband_transcript_variant_effect, transcript_variant_af_max, variant_polyphen,
                 variant_sift, transcript_variant_hgvs_c, transcript_variant_hgvs_p, transcript_variant_hgvs_g):
        self.case_id = case_id
        self.variant_count = variant_count
        self.gene_ensembl_id = gene_ensembl_id
        self.gene_hgnc_name = gene_hgnc_name
        self.transcript_name = transcript_name
        self.transcript_canonical = transcript_canonical
        self.transcript_strand = transcript_strand
        self.proband_transcript_variant_effect = proband_transcript_variant_effect
        self.transcript_variant_af_max = transcript_variant_af_max
        self.variant_polyphen = variant_polyphen
        self.variant_sift = variant_sift
        self.transcript_variant_hgvs_c = transcript_variant_hgvs_c
        self.transcript_variant_hgvs_p = transcript_variant_hgvs_p
        self.transcript_variant_hgvs_g = transcript_variant_hgvs_g
        self.gene_model = None


# old version without using tempfile:
# def generate_vcf(variants):
#     with open('temp.vcf', 'w') as vcffile:
#         f = csv.writer(vcffile, delimiter='\t')
#         for variant in variants:
#             f.writerow([variant.chromosome, variant.position, variant.case_id + ":" + variant.variant_count,
#                         variant.ref, variant.alt])

# new version using tempfile:
def generate_vcf(variants):
    tmpvcf = tempfile.NamedTemporaryFile(mode='w+t', delete=False)
    for variant in variants:
        row_to_write = str(variant.chromosome) + '\t' + str(variant.position) + '\t' + str(variant.case_id) + ":" + \
                       str(variant.variant_count) + '\t' + variant.ref + '\t' + variant.alt + '\n'
        tmpvcf.writelines(row_to_write)
    print(tmpvcf.name)
    return tmpvcf.name

#old version without using tempfile
# def run_vep():
#     config_dict = load_config.LoadConfig().load()
#     # builds command from locations supplied in config file
#     cmd = "{vep} -i temp.vcf -o temp.vep.vcf --cache --dir_cache {cache} --fork 4 --vcf --flag_pick \
#             --exclude_predicted --everything --dont_skip --total_length --offline --fasta {fasta_loc}".format(
#         vep=config_dict['vep'],
#         cache=config_dict['cache'],
#         fasta_loc=config_dict['fasta_loc'],
#     )
#     os.system(cmd)

# new version using tempfile
def run_vep(infile):
    config_dict = load_config.LoadConfig().load()
    outfile = tempfile.NamedTemporaryFile(mode='w+t', delete=False)
    # builds command from locations supplied in config file
    cmd = "{vep} -i {infile} -o {outfile} --force_overwrite --cache --dir_cache {cache} --fork 4 --vcf --flag_pick \
            --exclude_predicted --everything --hgvsg --dont_skip --total_length --offline --fasta {fasta_loc}".format(
        vep=config_dict['vep'],
        infile=infile,
        outfile=outfile.name,
        cache=config_dict['cache'],
        fasta_loc=config_dict['fasta_loc'],
    )
    subprocess.Popen(cmd, stderr=subprocess.STDOUT, shell=True).wait()
    print(outfile.name)
    return outfile.name

def parse_vep_annotations(infile=None):
    if infile is not None:
        variants = parse_vep.ParseVep().read_file(infile)
    else:
        #reads in the local file saved in root folder for testing purposes
        variants = parse_vep.ParseVep().read_file('temp.vep.vcf')
    transcripts_list = []
    for variant in variants:
        case_id = variant['id'].split(":")[0]
        variant_count = variant['id'].split(":")[1]
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
            transcript_variant_af_max = variant['transcript_data'][transcript]['MAX_AF']
            variant_polyphen = variant['transcript_data'][transcript]['PolyPhen']
            variant_sift = variant['transcript_data'][transcript]['SIFT']
            transcript_variant_hgvs_c = variant['transcript_data'][transcript]['HGVSc']
            transcript_variant_hgvs_p = variant['transcript_data'][transcript]['HGVSp']
            transcript_variant_hgvs_g = variant['transcript_data'][transcript]['HGVSg']
            case_transcript = CaseTranscript(case_id, variant_count, gene_id, gene_name, transcript_name, canonical,
                                             transcript_strand, proband_transcript_variant_effect,
                                             transcript_variant_af_max, variant_polyphen, variant_sift,
                                             transcript_variant_hgvs_c, transcript_variant_hgvs_p,
                                             transcript_variant_hgvs_g)
            transcripts_list.append(case_transcript)
    return transcripts_list

# likely wont be needed when using tempfile
def remove_temp_files():
    os.system("rm temp.vcf temp.vep.vcf temp.vep.vcf_summary.txt")

def generate_transcripts(variant_list):
    #variant_list = get_variants()
    # variant_file = generate_vcf(variant_list)
    # annotated_file = run_vep(variant_file)
    # transcript_list = parse_vep_annotations(annotated_file)

    # bypassing running VEP
    transcript_list = parse_vep_annotations()

    #remove_temp_files()
    return transcript_list

