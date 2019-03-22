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

class CaseCNV:
    def __init__(self, chromosome, sv_start, sv_end, case_id, sv_type, genome_build):
        self.chromosome = chromosome
        self.sv_start = sv_start
        self.sv_end = sv_end
        self.case_id = case_id
        self.sv_type = sv_type
        self.genome_build = genome_build

class CaseSTR:
    def __init__(self, chromosome, str_start, str_end, repeated_sequence, normal_threshold, pathogenic_threshold, case_id, genome_build):
        self.chromosome = chromosome
        self.str_start = str_start
        self.str_end = str_end
        self.repeated_sequence = repeated_sequence
        self.normal_threshold = normal_threshold
        self.pathogenic_threshold = pathogenic_threshold
        self.case_id = case_id
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
    '''
    Function which creates a VCF formatted file from variant objects specified from MCA.
    :param variants: List of CaseVariant objects
    :return: A dict of 2 vcfs. Keys are hg19_vcf and hg38_vcf which releate to the different
    genome builds
    '''
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
    '''
    Function which runs VEP using subprocess. Takes multiple options from config.txt file
    :param infile: Dict containing VCFs for the 2 genome builds
    :param config_dict: Configuration dict
    :return: Dict which contains the locations of the 2 results files relating to the 2 genome builds
    '''
    hg19_vcf = infile['hg19_vcf']
    hg38_vcf = infile['hg38_vcf']
    hg19_outfile = tempfile.NamedTemporaryFile(mode='w+t', delete=False)
    hg38_outfile = tempfile.NamedTemporaryFile(mode='w+t', delete=False)
    # run VEP for hg19 variants
    annotated_variant_dict = {}


    if os.stat(hg19_vcf).st_size != 0: # if file not empty
        # builds command from locations supplied in config file
        cmd = "{vep} -i {infile} -o {outfile} --species homo_sapiens --force_overwrite --cache --dir_cache {cache} " \
              "--fork 4 --vcf --flag_pick --exclude_predicted --assembly GRCh37 --everything " \
              "--hgvsg --dont_skip --total_length --offline --fasta {fasta_loc} --cache_version {cache_version}".format(
                vep=config_dict['vep'],
                infile=hg19_vcf,
                outfile=hg19_outfile.name,
                cache=config_dict['cache'],
                cache_version=config_dict['cache_version'],
                fasta_loc=config_dict['hg19_fasta_loc'],
        )
        if config_dict["mergedVEP"] == 'True':
            cmd += ' --merged'
            subprocess.run(cmd, stderr=subprocess.STDOUT, shell=True, check=True)
        annotated_variant_dict['hg19_vep'] = hg19_outfile.name
    # run VEP for hg38 variants
    if os.stat(hg38_vcf).st_size != 0:
        cmd = "{vep} -i {infile} -o {outfile} --species homo_sapiens --force_overwrite --cache --dir_cache {cache}" \
              " --fork 4 --vcf --flag_pick  --exclude_predicted --assembly GRCh38 --everything " \
              "--hgvsg --dont_skip --total_length --offline --fasta {fasta_loc} --cache_version {cache_version}".format(
                vep=config_dict['vep'],
                infile=hg38_vcf,
                outfile=hg38_outfile.name,
                cache=config_dict['cache'],
                cache_version=config_dict['cache_version'],
                fasta_loc=config_dict['hg38_fasta_loc'],
        )
        if config_dict["mergedVEP"] == 'True':
            cmd += ' --merged'
        subprocess.run(cmd, stderr=subprocess.STDOUT, shell=True, check=True)
        annotated_variant_dict['hg38_vep'] = hg38_outfile.name
    return annotated_variant_dict


def run_vep_remotely(infile, config_dict):
    '''
    Function which runs VEP using paramiko on a remote machine.
    :param infile: Dict containing VCFs for the 2 genome builds
    :param config_dict: Configuration dict
    :return: Dict which contains the locations of the 2 results files relating to the 2 genome builds
    '''
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # builds command from locations supplied in config file
    ssh.connect(config_dict['remote_ip'],
                username=config_dict['remote_username'],
                password=config_dict['remote_password'])
    sftp = ssh.open_sftp()
    # run VEP for hg19 variants
    annotated_variant_dict = {}

    if not os.path.isdir('VEP'):
        os.makedirs('VEP')

    if 'hg19_vcf' in infile:
        hg19_vcf = infile['hg19_vcf']
        hg19_outfile = 'VEP/hg19_results.vcf'
        if os.stat(hg19_vcf).st_size != 0:
            sftp.put(hg19_vcf, '{remote_destination}/hg19_destination_file.txt'.format(
                remote_destination=config_dict['remote_directory']
            ))

            cmd = "{vep} -i {remote_destination}/hg19_destination_file.txt " \
                  " -o {remote_destination}/hg19_output.txt --species homo_sapiens --cache_version {cache_version} "  \
                  " --force_overwrite --cache --dir_cache {cache} --fork 4 --vcf --flag_pick --assembly GRCh37 " \
                  " --exclude_predicted --everything --hgvsg --dont_skip --total_length --offline --fasta {fasta_loc} ".format(
                    vep=config_dict['vep'],
                    cache=config_dict['cache'],
                    fasta_loc=config_dict['hg19_fasta_loc'],
                    cache_version=config_dict['cache_version'],
                    remote_destination=config_dict['remote_directory']

            )
            if config_dict["mergedVEP"] == 'True':
                cmd += ' --merged'
            stdin, stdout, stderr = ssh.exec_command(cmd)

            print('stdin:', stdin, 'stdout:', stdout.read(), 'stderr:', stderr.read())
            sftp.get('{remote_destination}/hg19_output.txt'.format(
                remote_destination=config_dict['remote_directory']), hg19_outfile
            )
            annotated_variant_dict['hg19_vep'] = hg19_outfile
    # run VEP for hg38 variants
    if 'hg38_vcf' in infile:
        hg38_vcf = infile['hg38_vcf']
        hg38_outfile = 'VEP/hg38_results.vcf'
        if os.stat(hg38_vcf).st_size != 0:
            sftp.put(hg38_vcf, '{remote_destination}/hg38_destination_file.txt'.format(
                remote_destination=config_dict['remote_directory']
            ))

            cmd = "{vep} -i {remote_destination}/hg38_destination_file.txt " \
                  " -o {remote_destination}/hg38_output.txt --species homo_sapiens --cache_version {cache_version} "  \
                  " --force_overwrite --cache --dir_cache {cache} --fork 4 --vcf --flag_pick --assembly GRCh38 " \
                  " --exclude_predicted --everything --hgvsg --dont_skip --total_length --offline --fasta {fasta_loc} ".format(
                    vep=config_dict['vep'],
                    cache=config_dict['cache'],
                    cache_version=config_dict['cache_version'],
                    fasta_loc=config_dict['hg38_fasta_loc'],
                    remote_destination=config_dict['remote_directory']
            )
            if config_dict["mergedVEP"] == 'True':
                cmd += ' --merged'
            stdin, stdout, stderr = ssh.exec_command(cmd)

            print('stdin:', stdin, 'stdout:', stdout.read(), 'stderr:', stderr.read())
            sftp.get('{remote_destination}/hg38_output.txt'.format(remote_destination=config_dict['remote_directory']),
                     hg38_outfile)
            annotated_variant_dict['hg38_vep'] = hg38_outfile

    sftp.close()
    ssh.close()
    return annotated_variant_dict


def parse_vep_annotations(infile=None):
    '''
    Takes the results from VEP and converts them into CaseTranscript objects which will then be passed to CAM for
    inserting into the database
    :param infile: Dict from run_vep function which contains VEP vcf file locations
    :return: List of CaseTranscript objects
    '''
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
                transcript_variant_hgvs_p = variant['transcript_data'][transcript]['HGVSp'].replace('%3D', '=')
                transcript_variant_hgvs_g = variant['transcript_data'][transcript]['HGVSg']
                case_transcript = CaseTranscript(case_id, variant_count, gene_id, gene_name, hgnc_id, transcript_name, canonical,
                                                 transcript_strand, proband_transcript_variant_effect,
                                                 transcript_variant_af_max, variant_polyphen, variant_sift,
                                                 transcript_variant_hgvs_c, transcript_variant_hgvs_p,
                                                 transcript_variant_hgvs_g)
                transcripts_list.append(case_transcript)
    return transcripts_list


def generate_transcripts(variant_list):
    '''
    Wrapper function for running VEP for MCA. This take as input a variant_list which contains all the variants
    for the cases which MCA will update/add. If bypass_VEP function is used from the config, this will read in
    the temp.vep.vcf file for transcripts
    :param variant_list: A list of Casevariant objects
    :return: A list of CaseTranscript objects for all the CaseVariants
    '''
    config_dict = load_config.LoadConfig().load()

    if config_dict["bypass_VEP"] == "True":
        print("Bypassing VEP")
        transcript_list = parse_vep_annotations()

    elif config_dict["bypass_VEP"] == "False":
        print("Running VEP")
        variant_vcf_dict = generate_vcf(variant_list)
        if config_dict['remoteVEP'] == 'True':
            annotated_files_dict = run_vep_remotely(variant_vcf_dict, config_dict)
        else:
            annotated_files_dict = run_vep(variant_vcf_dict, config_dict)
        transcript_list = parse_vep_annotations(annotated_files_dict)

    return transcript_list