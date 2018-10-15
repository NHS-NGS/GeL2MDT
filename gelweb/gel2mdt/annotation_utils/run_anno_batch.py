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
from pycellbase.cbclient import CellBaseClient
import random
from datetime import datetime
os.environ['UTA_DB_URL'] = 'postgresql://anonymous@localhost:5432/uta/uta_20171026'
import hgvs
import hgvs.parser
import hgvs.assemblymapper
import hgvs.dataproviders.uta
hp = hgvs.parser.Parser()
hdp = hgvs.dataproviders.uta.connect()
import re


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


def get_variant_list(variants):
    '''
    Function which creates a list from variant objects specified from MCA.

    :param variants: List of CaseVariant objects
    :return: variant_dict: A dict of lists. Keys are GRCh37 and GRCh38 which releate to the different genome builds
    :return: A dict with translations of original variants to their string representations
    '''

    grch37_variant_list = []
    grch38_variant_list = []
    variant_reference = {}
    for variant in variants:
        print(variant.genome_build)
        ref = variant.ref
        alt = variant.alt
        pos = int(variant.position)
        if len(alt) > 1:
            if len(ref) == 1:  # This is a insertion
                ref = ''
                alt = alt[1:]
                pos += 1
        elif len(ref) > 1:
            if len(alt) == 1:  # This is a deletion
                ref = ref[1:]
                alt = ''
                pos += 1
        if 'GRCh37' in variant.genome_build:
            grch37_variant_list.append(f"{variant.chromosome}:{pos}:{ref}:{alt}")
            random.shuffle(grch37_variant_list)
        elif 'GRCh38' in variant.genome_build:
            grch38_variant_list.append(f"{variant.chromosome}:{pos}:{ref}:{alt}")
            random.shuffle(grch38_variant_list)
        variant_reference[variant] = f"{variant.chromosome}:{pos}:{ref}:{alt}"

    variant_dict = {'GRCh37': grch37_variant_list, 'GRCh38': grch38_variant_list}
    return variant_dict, variant_reference


def run_cellbase(variant_dict):
    '''
    Runs cellbase to get annotation
    :param variant_dict: Dict with keys as assemblies and values are variants in string format
    :return: dictionary with keys are assemblies and values as json results from cellbase
    '''
    cbc = CellBaseClient()
    vc = cbc.get_variant_client()
    annotated_dict = {}
    print(variant_dict)
    for key in variant_dict:
        variants_info = vc.get_annotation(variant_dict[key], assembly=key)
        annotated_dict[key] = variants_info
    return annotated_dict


def parse_cellbase(variants_list, annotated_variants_dict, variant_reference):
    '''

    :param variants_list: A list of CaseVariants to be annotated
    :param annotated_variants_dict: A dict from run_cellbase with the annotated variants jsons
    :param variant_reference: A dict with translations of CaseVariants to their string representations
    :return: A list of CaseTranscript objects which are returned to MCA
    '''
    transcript_list = []
    for variant in variants_list:
        for annotated_variant in annotated_variants_dict[variant.genome_build]:
            if annotated_variant['id'] == variant_reference[variant]:
                for result in annotated_variant['result']:  # Not sure why there would be 2 results
                    count = 0
                    for consequence in result['consequenceTypes']:  # Again no idea why a list
                        canonical = count == 0
                        transcript_variant_af_max = 0  # Dont have this
                        hgnc_id = None  # Don't have this
                        proband_transcript_variant_effect = None
                        variant_polyphen = None
                        variant_sift = None
                        transcript_variant_hgvs_c = ''
                        transcript_variant_hgvs_p = ''
                        required_fields = ['ensemblGeneId', 'geneName', 'ensemblTranscriptId', 'strand',
                                           'sequenceOntologyTerms']
                        if all([f in consequence for f in required_fields]):
                            gene_id = consequence['ensemblGeneId']
                            gene_name = consequence['geneName']
                            transcript_name = consequence['ensemblTranscriptId']
                            transcript_strand = consequence['strand']
                            try:
                                for consequence_types in consequence['sequenceOntologyTerms']:
                                    proband_transcript_variant_effect = consequence_types['name']
                                    break
                            except KeyError:
                                pass
                            try:
                                for scores in consequence['proteinVariantAnnotation']['substitutionScores']:
                                    if scores['source'] == 'sift':
                                        variant_sift = f"{scores['description']}({scores['score']})"
                                    elif scores['source'] == 'polyphen':
                                        variant_polyphen = f"{scores['description']}({scores['score']})"
                            except KeyError:
                                pass
                            try:
                                for hgvs_code in result['hgvs']:
                                    if hgvs_code.startswith(transcript_name):
                                        transcript_variant_hgvs_c = hgvs_code
                                        break
                            except KeyError:
                                pass
                            if transcript_variant_hgvs_c:
                                try:
                                    transcript_variant_hgvs_c = re.sub(r'\([^)]*\)', '', transcript_variant_hgvs_c)
                                    var_c1 = hp.parse_hgvs_variant(transcript_variant_hgvs_c)
                                    print(str(var_c1))
                                    am = hgvs.assemblymapper.AssemblyMapper(hdp,
                                                                            assembly_name=variant.genome_build,
                                                                            alt_aln_method='splign',
                                                                            replace_reference=False)
                                    var_p = am.c_to_p(var_c1)
                                    print(var_p)
                                    transcript_variant_hgvs_p = str(var_p)
                                except (hgvs.exceptions.HGVSInvalidVariantError,
                                        hgvs.exceptions.HGVSUsageError,
                                        NotImplementedError,
                                        TypeError,
                                        hgvs.exceptions.HGVSDataNotAvailableError) as e:
                                    print(e)
                            transcript_variant_hgvs_g = f"{variant.chromosome}:g.{variant.position}" \
                                                        f"{variant.ref}>{variant.alt}"  # Ugly hack
                            case_transcript = CaseTranscript(variant.case_id,
                                                             variant.variant_count,
                                                             gene_id,
                                                             gene_name,
                                                             hgnc_id,
                                                             transcript_name,
                                                             canonical,
                                                             transcript_strand, proband_transcript_variant_effect,
                                                             transcript_variant_af_max, variant_polyphen, variant_sift,
                                                             transcript_variant_hgvs_c, transcript_variant_hgvs_p,
                                                             transcript_variant_hgvs_g)
                            transcript_list.append(case_transcript)
                            count += 1
    return transcript_list


def generate_transcripts(variant_list):
    '''
    Wrapper function for running VEP for MCA. This take as input a variant_list which contains all the variants
    for the cases which MCA will update/add. If bypass_VEP function is used from the config, this will read in
    the temp.vep.vcf file for transcripts

    :param variant_list: A list of Casevariant objects
    :return: A list of CaseTranscript objects for all the CaseVariants
    '''
    variant_vcf_dict, variant_reference = get_variant_list(variant_list)
    annotated_dict = run_cellbase(variant_vcf_dict)
    transcripts_list = parse_cellbase(variant_list, annotated_dict, variant_reference)
    return transcripts_list
