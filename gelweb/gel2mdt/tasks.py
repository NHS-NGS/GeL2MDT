import requests
from bs4 import BeautifulSoup
import os
from .api_utils.poll_api import PollAPI
from .vep_utils import run_vep_batch
from .models import *
from .database_utils.multiple_case_adder import GeneManager, MultipleCaseAdder
from gelweb.celery import app
from celery.schedules import crontab
from celery.task import periodic_task
import json
from json import JSONDecodeError
import labkey as lk
from datetime import datetime
import time

def get_gel_content(ir, ir_version):
    # otherwise get uname and password from a file

    interpretation_reponse = PollAPI(
        "cip_api_for_report", f'interpretationRequests/{ir}/{ir_version}/')
    interp_json = interpretation_reponse.get_json_response()

    analysis_versions = []
    latest = None
    if 'interpreted_genome' in interp_json:
        for cip_version in interp_json['interpreted_genome']:
            analysis_versions.append(cip_version['cip_version'])
        try:
            latest = max(analysis_versions)
        except ValueError as e:
            latest = 1

    html_report = PollAPI(
        "cip_api_for_report", f"ClinicalReport/{ir}/{ir_version}/{latest}/"
    )
    gel_content = html_report.get_json_response(content=True)
    try:
        gel_json_content = json.loads(gel_content)
        if gel_json_content['detail'].startswith('Not found'):
            return None
    except JSONDecodeError as e:
        pass

    analysis_panels = {}

    panel_app_panel_query_version = 'https://bioinfo.extge.co.uk/crowdsourcing/WebServices/get_panel/{panelhash}/?version={version}'
    if 'pedigree' in interp_json['interpretation_request_data']['json_request']:
        if interp_json['interpretation_request_data']['json_request']['pedigree']['analysisPanels']:
            for panel_section in interp_json['interpretation_request_data']['json_request']['pedigree']['analysisPanels']:
                panel_name = panel_section['panelName']
                version = panel_section['panelVersion']
                analysis_panels[panel_name] = {}
                panel_details = requests.get(panel_app_panel_query_version.format(panelhash=panel_name, version=version),
                                             verify=False).json()
                analysis_panels[panel_name][panel_details['result']['SpecificDiseaseName']] = []
                for gene in panel_details['result']['Genes']:
                    analysis_panels[panel_name][panel_details['result']['SpecificDiseaseName']].append(gene['GeneSymbol'])

    gene_panels = {}
    for panel, details in analysis_panels.items():
        gene_panels.update(details)

    gel_content = BeautifulSoup(gel_content)

    try:
        # remove any warning signs if they appear in the report
        disclaimer = gel_content.find("div", {"class": "content-div error-panel"}).extract()
    except:
        pass
    # Find the annex header
    annex = gel_content.find("div", {"class": "annex-banner content-div"})

    # Add a div for the panels  Table tag to be inserted after the report annex
    div_tag = gel_content.new_tag("div")
    div_tag['class'] = "content-div"
    if annex:
        annex.insert_after(div_tag)

    # panel_keys = fake_panels.keys()
    panel_keys = list(gene_panels.keys())

    table_tag = gel_content.new_tag("table")

    h3_tag = gel_content.new_tag("h3")
    h3_tag.string = 'Gene Panel Specification'

    # Table headers and table rows to be inserted after the table tag
    # tags created to shamelessly rip off the GeL formatting
    thead_tag = gel_content.new_tag("thead")
    tr_tag = gel_content.new_tag("tr")
    th1_tag = gel_content.new_tag("th")
    th2_tag = gel_content.new_tag("th")

    th1_tag.string = 'Genepanel'
    th2_tag.string = 'Genes'
    tr_tag.insert(1, th1_tag)
    tr_tag.insert(2, th2_tag)
    thead_tag.insert(1, tr_tag)
    table_tag.insert(1, thead_tag)

    tbody_tag = gel_content.new_tag("tbody")

    for panel in range(len(panel_keys)):
        # get the actual name of the panel
        panel_name = panel_keys[panel]
        panel_genes = gene_panels[panel_name]

        tr_tag = gel_content.new_tag("tr")
        td_panel = gel_content.new_tag("td")
        td_panel['width'] = '20%'
        td_genes = gel_content.new_tag("td")
        td_panel.string = panel_name
        td_genes.string = ', '.join(panel_genes)
        tr_tag.insert(1, td_panel)
        tr_tag.insert(2, td_genes)
        tbody_tag.insert(panel, tr_tag)

    table_tag.insert(2, tbody_tag)

    div_tag.insert(1, h3_tag)
    div_tag.insert(2, table_tag)

    return gel_content.prettify()

def panel_app(gene_panel, gp_version):
    gene_list = []
    panel_app_panel_query_version = 'https://bioinfo.extge.co.uk/crowdsourcing/WebServices/get_panel/{gene_panel}/?version={gp_version}'
    panel_details = requests.get(
        panel_app_panel_query_version.format(gene_panel=gene_panel, gp_version=gp_version), verify=False).json()

    for gene in panel_details['result']['Genes']:
        gene_list.append(gene['GeneSymbol'])
    gene_panel_info = {'gene_list': gene_list, 'panel_length': len(gene_list)}
    return gene_panel_info

@app.task
def update_for_t3(report_id):
    report = GELInterpretationReport.objects.get(id=report_id)
    mca = MultipleCaseAdder(pullt3=True, sample=report.ir_family.participant_family.proband.gel_id)
    mca.update_database()

@periodic_task(run_every=crontab(minute=0, hour=0))
def update_cases():
    mca = MultipleCaseAdder(pullt3=False, skip_demographics=False)
    mca.update_database()


class VariantAdder(object):
    """
    Class for adding single variants to a case
    """
    def __init__(self, report, variant, variant_entry):
        self.report = report
        self.variant_entry = variant_entry
        self.variants = [variant]
        self.transcripts = None
        self.gene_manager = GeneManager
        self.gene_entries = []
        self.transcript_entries = []
        self.proband_variant = None

        self.run_vep()
        self.insert_genes()
        self.insert_transcripts()
        self.insert_transcript_variants()
        self.insert_proband_variant()
        self.insert_proband_transcript_variant()

    def run_vep(self):
        self.transcripts = run_vep_batch.generate_transcripts(self.variants)

    def insert_genes(self):
        gene_list = []
        for transcript in self.transcripts:
            if transcript.gene_ensembl_id and transcript.gene_hgnc_id:
                gene_list.append({
                    'ensembl_id': transcript.gene_ensembl_id,
                    'hgnc_name': transcript.gene_hgnc_name,
                    'hgnc_id': str(transcript.gene_hgnc_id),
                })

        for gene in gene_list:
            p, created = Gene.objects.get_or_create(hgnc_id=gene['hgnc_id'],
                                                    defaults={'hgnc_name':gene['hgnc_name'],
                                                              'ensembl_id': gene['ensembl_id']})
            self.gene_entries.append(p)

    def insert_transcripts(self):
        for transcript in self.transcripts:
            # convert canonical to bools:
            transcript.canonical = transcript.transcript_canonical == "YES"
            if not transcript.gene_hgnc_id:
                # if the transcript has no recognised gene associated
                continue  # don't bother checking genes
            transcript.gene_model = None
            for gene in self.gene_entries:
                if gene.hgnc_id == transcript.gene_hgnc_id:
                    transcript.gene_model = gene

            for transcript in self.transcripts:
                if transcript.gene_model:
                    p, created = Transcript.objects.get_or_create(name=transcript.transcript_name,
                                                                  genome_assembly=self.report.assembly,
                                                                  defaults={'gene': transcript.gene_model,
                                                                            'canonical_transcript':transcript.canonical,
                                                                            'strand': transcript.transcript_strand
                                                                            })
                    self.transcript_entries.append(p)

    def insert_transcript_variants(self):
        for transcript in self.transcripts:
            transcript.variant_entry = self.variant_entry

            # add the corresponding Transcript entry
            for transcript_entry in self.transcript_entries:
                found = False
                if transcript_entry.name == transcript.transcript_name and transcript_entry.genome_assembly == self.report.assembly:
                    transcript.transcript_entry = transcript_entry
                    found = True
                    break
                if not found:
                    # we don't make entries for tx with no Gene
                    transcript.transcript_entry = None
        for transcript in self.transcripts:
            if transcript.transcript_entry:
                p, created = TranscriptVariant.objects.get_or_create(transcript=transcript.transcript_entry,
                                                                     variant=transcript.variant_entry,
                                                                     defaults={'af_max': transcript.gene_model,
                                                                        "af_max": transcript.transcript_variant_af_max,
                                                                        "hgvs_c": transcript.transcript_variant_hgvs_c,
                                                                        "hgvs_p": transcript.transcript_variant_hgvs_p,
                                                                        "hgvs_g": transcript.transcript_variant_hgvs_g,
                                                                        "sift": transcript.variant_sift,
                                                                        "polyphen": transcript.variant_polyphen})

    def insert_proband_variant(self):
        p, created = ProbandVariant.objects.get_or_create(
            interpretation_report=self.report,
            variant=self.variant_entry,
            defaults={"max_tier": 0,
                        "zygosity": "unknown",
                        "maternal_zygosity": "unknown",
                        "paternal_zygosity": "unknown",
                        "inheritance": "unknown",
                        "somatic": False})
        self.proband_variant = p

    def insert_proband_transcript_variant(self):
        for transcript in self.transcripts:
            if self.proband_variant.variant == transcript.variant_entry:
                transcript.proband_variant_entry = self.proband_variant
        for transcript in self.transcripts:
            if transcript.transcript_entry and transcript.proband_variant_entry:
                p, created = ProbandTranscriptVariant.objects.get_or_create(transcript=transcript.transcript_entry,
                                                                            proband_variant=transcript.proband_variant_entry,
                                                                     defaults={"selected": transcript.transcript_entry.canonical_transcript,
                                                                                "effect": transcript.proband_transcript_variant_effect})


class UpdateDemographics(object):
    def __init__(self, report_id):
        self.report = GELInterpretationReport.objects.get(id=report_id)
        self.clinician = None
        config_dict = load_config.LoadConfig().load()
        # poll labkey
        labkey_server_request = config_dict['labkey_server_request']
        self.server_context = lk.utils.create_server_context(
            'gmc.genomicsengland.nhs.uk',
            labkey_server_request,
            '/labkey', use_ssl=True)

    def update_clinician(self):
        clinician_details = {}
        search_results = lk.query.select_rows(
            server_context=self.server_context,
            schema_name='gel_rare_diseases',
            query_name='rare_diseases_registration',
            filter_array=[
                lk.query.QueryFilter('family_id',
                                     self.report.ir_family.participant_family.gel_family_id,
                                     'contains')
            ]
        )
        try:
            clinician_details['name'] = search_results['rows'][0].get(
                'consultant_details_full_name_of_responsible_consultant')
        except IndexError as e:
            pass
        try:
            clinician_details['hospital'] = search_results['rows'][0].get(
                'consultant_details_hospital_of_responsible_consultant')
        except IndexError as e:
            pass

        if 'name' in clinician_details and 'hospital' in clinician_details:
            clinician, saved = Clinician.objects.get_or_create(name= clinician_details['name'],
                                                                defaults={
                                                                "email": "unknown",  # clinicain email not on labkey
                                                                "hospital": clinician_details['hospital'],
                                                                "added_by_user": False})
            self.clinician = clinician
            family = self.report.ir_family.participant_family
            family.clinician = clinician
            family.save()
            return clinician
        else:
            return None

    def update_demographics(self):
        participant_demographics = {
            "surname": 'unknown',
            "forename": 'unknown',
            "date_of_birth": '2011/01/01',  # unknown but needs to be in date format
            "nhs_num": 'unknown',
        }

        search_results = lk.query.select_rows(
            server_context=self.server_context,
            schema_name='gel_rare_diseases',
            query_name='participant_identifier',
            filter_array=[
                lk.query.QueryFilter(
                    'participant_id', self.report.ir_family.participant_family.proband.gel_id, 'contains')
            ]
        )
        try:
            participant_demographics["surname"] = search_results['rows'][0].get(
                'surname')
        except IndexError as e:
            pass
        try:
            participant_demographics["forename"] = search_results['rows'][0].get(
                'forenames')
        except IndexError as e:
            pass
        try:
            participant_demographics["date_of_birth"] = search_results['rows'][0].get(
                'date_of_birth').split(' ')[0]
        except IndexError as e:
            pass
        try:
            if search_results['rows'][0].get('person_identifier_type').upper() == "NHSNUMBER":
                participant_demographics["nhs_num"] = search_results['rows'][0].get(
                    'person_identifier')
        except IndexError as e:
            pass

        search_results = lk.query.select_rows(
            server_context=self.server_context,
            schema_name='gel_rare_diseases',
            query_name='rare_diseases_diagnosis',
            filter_array=[
                lk.query.QueryFilter('participant_identifiers_id',
                                     self.report.ir_family.participant_family.proband.gel_id, 'eq')
            ]
        )

        recruiting_disease = None
        try:
            recruiting_disease = search_results['rows'][0].get('gel_disease_information_specific_disease', None)
        except IndexError as e:
            pass

        if participant_demographics['surname'] != 'unknown' and participant_demographics['nhs_num'] != 'unknown':
            proband = self.report.ir_family.participant_family.proband
            proband.nhs_number = participant_demographics['nhs_num']
            proband.surname = participant_demographics['surname']
            proband.forename = participant_demographics['forename']
            proband.date_of_birth = datetime.strptime(participant_demographics["date_of_birth"],
                                                               "%Y/%m/%d").date()
            proband.recruiting_disease = recruiting_disease
            proband.save()
            return proband
        else:
            return None

