import os
import tempfile
import subprocess
import csv
from ..config import load_config
from . import parse_vep
import paramiko

class CaseVariant:
    def __init__(self, chromosome, position, case_id, variant_count, ref, alt, genome_build):
        self.chromosome = chromosome
        self.position = position
        self.case_id = case_id
        self.variant_count = variant_count
        self.ref = ref
        self.alt = alt
        self.genome_build = genome_build

class CaseTranscript:
    def __init__(self, case_id, variant_count, gene_ensembl_id, gene_hgnc_name, gene_hgnc_id, transcript_name, transcript_canonical,
                 transcript_strand, proband_transcript_variant_effect, transcript_variant_af_max, variant_polyphen,
                 variant_sift, transcript_variant_hgvs_c, transcript_variant_hgvs_p, transcript_variant_hgvs_g):
        self.case_id = case_id
        self.variant_count = variant_count
        self.gene_ensembl_id = gene_ensembl_id
        self.gene_hgnc_name = gene_hgnc_name
        self.gene_hgnc_id = gene_hgnc_id
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
        self.transcript_entry = None
        self.proband_variant_entry = None
        self.selected = False


def generate_vcf(variants):
    tmphg19 = tempfile.NamedTemporaryFile(mode='w+t', delete=False)
    tmphg38 = tempfile.NamedTemporaryFile(mode='w+t', delete=False)
    for variant in variants:
        if 'GRCh37' in variant.genome_build:
            row_to_write = str(variant.chromosome) + '\t' + str(variant.position) + '\t' + str(variant.case_id) + ":" + \
                           str(variant.variant_count) + '\t' + variant.ref + '\t' + variant.alt + '\n'
            tmphg19.writelines(row_to_write)
        elif 'GRCh38' in variant.genome_build:
            row_to_write = str(variant.chromosome) + '\t' + str(variant.position) + '\t' + str(variant.case_id) + ":" + \
                           str(variant.variant_count) + '\t' + variant.ref + '\t' + variant.alt + '\n'
            tmphg38.writelines(row_to_write)
    tmphg19.close()
    tmphg38.close()
    print(tmphg19.name, tmphg38.name)
    variant_dict = {'hg19_vcf': tmphg19.name, 'hg38_vcf': tmphg38.name}
    return variant_dict

def run_vep(infile, config_dict):
    hg19_vcf = infile['hg19_vcf']
    hg38_vcf = infile['hg38_vcf']
    hg19_outfile = tempfile.NamedTemporaryFile(mode='w+t', delete=False)
    hg38_outfile = tempfile.NamedTemporaryFile(mode='w+t', delete=False)
    # run VEP for hg19 variants
    annotated_variant_dict = {}
    if os.stat(hg19_vcf).st_size != 0: # if file not empty
        # builds command from locations supplied in config file
        cmd = "{vep} -i {infile} -o {outfile} --force_overwrite --cache --dir_cache {cache} --fork 4 --vcf --flag_pick \
                --exclude_predicted --everything --hgvsg --dont_skip --total_length --offline --fasta {fasta_loc}".format(
            vep=config_dict['vep'],
            infile=hg19_vcf,
            outfile=hg19_outfile.name,
            cache=config_dict['hg19_cache'],
            fasta_loc=config_dict['hg19_fasta_loc'],
        )
        subprocess.Popen(cmd, stderr=subprocess.STDOUT, shell=True).wait()
        annotated_variant_dict['hg19_vep'] = hg19_outfile.name
    # run VEP for hg38 variants
    if os.stat(hg38_vcf).st_size != 0:
        cmd = "{vep} -i {infile} -o {outfile} --force_overwrite --cache --dir_cache {cache} --fork 4 --vcf --flag_pick \
                    --exclude_predicted --everything --hgvsg --dont_skip --total_length --offline --fasta {fasta_loc}".format(
            vep=config_dict['vep'],
            infile=hg38_vcf,
            outfile=hg38_outfile.name,
            cache=config_dict['hg38_cache'],
            fasta_loc=config_dict['hg38_fasta_loc'],
        )
        subprocess.Popen(cmd, stderr=subprocess.STDOUT, shell=True).wait()
        annotated_variant_dict['hg38_vep'] = hg38_outfile.name
    return annotated_variant_dict

def run_vep_gosh(infile, config_dict):
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # builds command from locations supplied in config file
    ssh.connect(config_dict['crick_ip'],
                username=config_dict['crick_username'],
                password=config_dict['crick_password'])
    sftp = ssh.open_sftp()
    # run VEP for hg19 variants
    annotated_variant_dict = {}
    if 'hg19_vcf' in infile:
        hg19_vcf = infile['hg19_vcf']
        hg19_outfile = 'VEP/hg19_results.vcf'
        if os.stat(hg19_vcf).st_size != 0:
            sftp.put(hg19_vcf, '/home/chris/gel2mdt_testing/hg19_destination_file.txt'.format(hg19_vcf))

            cmd = "{vep} -i /home/chris/gel2mdt_testing/hg19_destination_file.txt " \
                  " -o /home/chris/gel2mdt_testing/hg19_output.txt --species homo_sapiens --merged "  \
                  " --force_overwrite --cache --dir_cache {cache} --fork 4 --vcf --flag_pick --assembly GRCh37 " \
                  " --exclude_predicted --everything --hgvsg --dont_skip --total_length --offline --fasta {fasta_loc} ".format(
                    vep=config_dict['vep'],
                    cache=config_dict['cache'],
                    fasta_loc=config_dict['hg19_fasta_loc'],
            )
            stdin, stdout, stderr = ssh.exec_command(cmd)
            # stdin, stdout, stderr = ssh.exec_command('{gosh_vep} help'.format(gosh_vep=config_dict['gosh_vep']))

            print('stdin:', stdin, 'stdout:', stdout.read(), 'stderr:', stderr.read())
            sftp.get('/home/chris/gel2mdt_testing/hg19_output.txt', hg19_outfile)
            annotated_variant_dict['hg19_vep'] = hg19_outfile
    # run VEP for hg38 variants
    if 'hg38_vcf' in infile:
        hg38_vcf = infile['hg38_vcf']
        hg38_outfile = 'VEP/hg38_results.vcf'
        if os.stat(hg38_vcf).st_size != 0:
            sftp.put(hg38_vcf, '/home/chris/gel2mdt_testing/hg38_destination_file.txt'.format(hg38_vcf))

            cmd = "{vep} -i /home/chris/gel2mdt_testing/hg38_destination_file.txt " \
                  " -o /home/chris/gel2mdt_testing/hg38_output.txt --species homo_sapiens --merged "  \
                  " --force_overwrite --cache --dir_cache {cache} --fork 4 --vcf --flag_pick --assembly GRCh38 " \
                  " --exclude_predicted --everything --hgvsg --dont_skip --total_length --offline --fasta {fasta_loc} ".format(
                    vep=config_dict['vep'],
                    cache=config_dict['cache'],
                    fasta_loc=config_dict['hg38_fasta_loc'],
            )
            stdin, stdout, stderr = ssh.exec_command(cmd)
            # stdin, stdout, stderr = ssh.exec_command('{gosh_vep} help'.format(gosh_vep=config_dict['gosh_vep']))

            print('stdin:', stdin, 'stdout:', stdout.read(), 'stderr:', stderr.read())
            sftp.get('/home/chris/gel2mdt_testing/hg38_output.txt', hg38_outfile)
            annotated_variant_dict['hg38_vep'] = hg38_outfile

    sftp.close()
    ssh.close()
    return annotated_variant_dict

def parse_vep_annotations(infile=None):
    transcripts_list = []
    if infile is not None:
        hg19_variants = []
        hg38_variants = []
        if 'hg19_vep' in infile:
            if os.stat(infile['hg19_vep']).st_size != 0:
                hg19_variants = parse_vep.ParseVep().read_file(infile['hg19_vep'])
        if 'hg38_vep' in infile:
            if os.stat(infile['hg38_vep']).st_size != 0:
                hg38_variants = parse_vep.ParseVep().read_file(infile['hg38_vep'])
        # concatenate the two lists of variant dictionaries
        variants = hg19_variants + hg38_variants

        for variant in variants:
            case_id = variant['id'].split(":")[0]
            variant_count = variant['id'].split(":")[1]
            for transcript in variant['transcript_data']:
                gene_id = variant['transcript_data'][transcript]['Gene']
                gene_name = variant['transcript_data'][transcript]['SYMBOL']
                hgnc_id = variant['transcript_data'][transcript]['HGNC_ID']
                if hgnc_id.startswith('HGNC:'):
                    hgnc_id = str(hgnc_id.split(':')[1])
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
                case_transcript = CaseTranscript(case_id, variant_count, gene_id, gene_name, hgnc_id, transcript_name, canonical,
                                                 transcript_strand, proband_transcript_variant_effect,
                                                 transcript_variant_af_max, variant_polyphen, variant_sift,
                                                 transcript_variant_hgvs_c, transcript_variant_hgvs_p,
                                                 transcript_variant_hgvs_g)
                transcripts_list.append(case_transcript)
    return transcripts_list

def generate_transcripts(variant_list):

    config_dict = load_config.LoadConfig().load()
    print(config_dict["bypass_VEP"], type(config_dict["bypass_VEP"]))

    if config_dict["bypass_VEP"] == "True":
        print("Bypassing VEP")
        transcript_list = parse_vep_annotations()

    elif config_dict["bypass_VEP"] == "False":
        print("Running VEP")
        variant_vcf_dict = generate_vcf(variant_list)
        if config_dict['center'] == 'GOSH':
            annotated_files_dict = run_vep_gosh(variant_vcf_dict, config_dict)
        else:
            annotated_files_dict = run_vep(variant_vcf_dict, config_dict)

        transcript_list = parse_vep_annotations(annotated_files_dict)

    return transcript_list

