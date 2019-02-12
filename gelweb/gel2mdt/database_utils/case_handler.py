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
import json
import hashlib
import labkey as lk
from datetime import datetime
from django.utils.dateparse import parse_date
import time
from ..models import *
from ..api_utils.poll_api import PollAPI
from ..vep_utils.run_vep_batch import CaseVariant, CaseTranscript
from ..config import load_config
import re
import copy
import pprint
from tqdm import tqdm
from protocols.reports_6_0_0 import InterpretedGenome, InterpretationRequestRD, CancerInterpretationRequest, ClinicalReport


class Case(object):
    """
    Entity object which represents a case and it's associated details.

    Cases are instantiated by MultipleCaseAdder with basic init attributes,
    then details will be added if the case information needs to be added to or
    updated in the DB.

    Attributes:
        json (dict): upon initialisation of the Case, this is the full json
            response from PollAPI. This is edited during the database update
            process to keep relevant information together in the datastructure.
        raw_json (dict): a deepcopy of the json, which remains unmodified, for
            the purpose of saving the json to disk once a Case has been added
            or updated in the database.
        json_case_data (dict): a sub-dict within the json which refers to the
            interpretation_request_data.
        json_request_data (dict): a sub-dict of json_case_data which holds the
            tiered variant information. case_data and request_data are set as
            attributes during init mostly to avoid long dict accessors in the
            code itself.
        request_id (str): the XXXX-X CIP-ID of the Interpretation Request.
        json_hash (str): the MD5 hash of the json file, which has been sorted
            to maintain consistency of values (which would change the hash).
        proband (dict): sub-dict of json which holds the information about the
            proband only.
        proband_sample (str): the sample ID used for sequencing of the proband,
            obtained from the JSON.
        family_members (list): list of sub-dicts of the json which hold
            information about all relatives of the proband's relative
        tools_and_versions (dict): k-v pair of tools used by GeL/CIP (key) and
            the version that was used (value)
        status (str): the status of the case according the CIP-API, choice of
            waiting_payload, interpretation_generated, dispatched, blocked,
            files_copied, transfer_ready, transfer_complete,
            rejected_wrong_format, gel_qc_failed, gel_qc_passed, sent_to_gmcs,
            report_generated, or report_sent.
        panel_manager (multiple_case_adder.PanelManager): instance of the class
            PanelManager, which is used to hold new panels polled from PanelApp
            during a cycle of the Cases' overseeing MultipleCaseAdder to avoid
            polling PanelApp for the same new panel twice, before it can be
            detected by check_found_in_db()
        variant_manager (multiple_case_adder.VariantManager): instance of the
            class VariantManager, which checks all variants from VEP 37 which
            can conflict with VEP 38, then ensures the same variant (ie at the
            same genomic position) has identical information between b37/b38
            cases.
        gene_manager (multiple_case_adder.GeneManager): instance of the control
            class GeneManager, which ensures that GeneNames is not polled twice
            for the same gene in one run of the MCA, ie. before a new gene is
            added the database and hence won't be found by check_found_in_db
        panels (dict): the "analysisPanels" section of the JSON. This only
            applies for rare disease cases; cancer cases do not have panels so
            this attribute is None in those cases.
        skip_demographics (bool): whether (T) or not (F) we should poll LabKey
            for demographic information for database entries. If not, Proband,
            Relative, and Clinician will have "unknown" set as their values for
            all LabKey-sourced fields.
        pullt3 (bool): whether (T) or not (F) Tier 3 variants should be pulled
            out of the JSON and added to the database. This is mostly to save
            time, since in the case of !pullt3, there will be a huge reduction
            in number of variants passed to VEP/variant annotater.
        attribute_managers (dict): k-v pairing of each database model being
            updated for each case, and the CaseAttributeManager for that model
            for this case (e.g. {gel2mdt.models.Proband: CaseAttributeManager}.
            attribute_managers are not created at first, so this starts as an
            empty dictionary. When MCA determines the case needs to be added or
            updated in the database, then the MCA will create (in the correct
            order) CaseAttributeManagers for each model type for each case.
    """
    def __init__(self, case_json, panel_manager, variant_manager, gene_manager, skip_demographics=False, pullt3=True):
        """
        Initialise a Case with the json, then pull out relevant sections.

        The JSON is deepcopied for raw_json, then the relevant sections are
        extracted by dictionary accessors or standalone functions (in the case
        of proband, family_members, tools_and_versions). A SHA512 hash is also
        calculated for the JSON, to later check if the JSON used for a case
        has changed in the CIP API.
        """

        self.json = case_json
        # raw json created to dump at the end; json attr is modified
        self.pullt3 = pullt3
        self.raw_json = copy.deepcopy(case_json)
        self.json_case_data = self.json["interpretation_request_data"]
        self.json_request_data = self.json_case_data["json_request"]
        self.request_id = str(
            self.json["interpretation_request_id"]) \
            + "-" + str(self.json["version"])
        if self.json["sample_type"] == 'raredisease':
            self.ir_obj = InterpretationRequestRD.fromJsonDict(self.json_request_data)
        elif self.json['sample_type'] == 'cancer':
            self.ir_obj = CancerInterpretationRequest.fromJsonDict(self.json_request_data)

        self.json_hash = self.hash_json()
        self.proband = self.get_proband_json()
        if self.json["sample_type"] == 'raredisease':
            self.proband_sample = self.proband.samples[0].sampleId
        elif self.json['sample_type'] == 'cancer':
            self.proband_sample = self.proband.matchedSamples[0].tumourSampleId
        self.family_members = self.get_family_members()
        self.tools_and_versions = {'genome_build': self.json["assembly"]}
        self.status = self.get_status_json()

        self.panel_manager = panel_manager
        self.variant_manager = variant_manager
        self.gene_manager = gene_manager

        self.panels = self.get_panels_json()

        self.ig_objs = []  # List of interpreteted genome objects
        self.clinical_report_objs = []  # ClinicalReport objects
        self.variants = self.get_case_variants()
        self.transcripts = []  # set by MCM with a call to vep_utils
        self.demographics = None
        self.clinicians = None
        self.diagnosis = None

        # initialise a dict to contain the AttributeManagers for this case,
        # which will be set by the MCA as they are required (otherwise there
        # are missing dependencies)
        self.skip_demographics = skip_demographics
        self.attribute_managers = {}

    def hash_json(self):
        """
        Hash the given json for this Case, sorting the keys to ensure
        that order is preserved, or else different order -> different
        hash.
        """
        hash_buffer = json.dumps(self.json, sort_keys=True).encode('utf-8')
        hash_hex = hashlib.sha512(hash_buffer)
        hash_digest = hash_hex.hexdigest()
        return hash_digest

    def get_proband_json(self):
        """
        Get the proband from the list of partcipants in the JSON.
        """
        proband_json = None
        if self.json["sample_type"]=='raredisease':
            proband_json = [member for member in self.ir_obj.pedigree.members if member.isProband][0]
        elif self.json["sample_type"]=='cancer':
            proband_json = self.ir_obj.cancerParticipant
        return proband_json

    def get_family_members(self):
        '''
        Gets the family member details from the JSON.
        :return: A list of dictionaries containing family member details (gel ID, relationship and affection status)
        '''
        family_members = []
        if self.json["sample_type"] == 'raredisease':
            for member in self.ir_obj.pedigree.members:
                if not member.isProband:
                    if member.additionalInformation:
                        relation = member.additionalInformation.get('relation_to_proband', 'unknown')
                    else:
                        relation = 'unknown'
                    family_member = {'gel_id': member.participantId,
                                     'relation_to_proband': relation,
                                     'affection_status': True if member.disorderList else False,
                                     'sequenced': True if member.samples else False,
                                     'sex': member.sex,
                                     }
                    family_members.append(family_member)
        return family_members

    def get_tools_and_versions(self):
        '''
        Gets the genome build from the JSON. Details of other tools (VEP, Polyphen/SIFT) to be pulled from config file?
        :return: A dictionary of tools and versions used for the case
        '''
        if self.json['sample_type'] == 'raredisease':
            if self.json_request_data['genomeAssemblyVersion'].startswith('GRCh37'):
                genome_build = 'GRCh37'
            elif self.json_request_data['genomeAssemblyVersion'].startswith('GRCh38'):
                genome_build = 'GRCh38'
        elif self.json['sample_type'] == 'cancer':
            if self.json["assembly"].startswith('GRCh37'):
                genome_build = 'GRCh37'
            elif self.json["assembly"].startswith('GRCh38'):
                genome_build = 'GRCh38'
        else:
            raise Exception(f'{self.request_id} has unknown genome build')

        return {'genome_build': genome_build}

    def get_status_json(self):
        """
        JSON has a list of statuses. Extract only the latest.
        """
        status_jsons = self.json["status"]
        return status_jsons[-1]  # assuming GeL will always work upwards..

    def get_panels_json(self):
        """
        Get the list of panels from the json
        """
        analysis_panels = []
        if self.json["sample_type"] == 'raredisease':
            analysis_panels = self.ir_obj.pedigree.analysisPanels
        return analysis_panels

    def get_case_variants(self):
        """
        Create CaseVariant objects for each variant listed in the json,
        then return a list of all CaseVariants for construction of
        CaseTranscripts using VEP.
        """
        json_variants = []
        case_variant_list = []
        # go through each variant in the json
        variant_object_count = 0
        genome_build = self.json['assembly']
        for ig in self.json['interpreted_genome']:
            ig_obj = InterpretedGenome.fromJsonDict(ig['interpreted_genome_data'])
            if ig_obj.variants:
                for variant in ig_obj.variants:
                    # Sort out tiers first
                    variant_min_tier = None
                    tier = None
                    for report_event in variant.reportEvents:
                        if self.json['sample_type'] == 'raredisease':
                            if report_event.tier:
                                tier = int(report_event.tier[-1])
                        elif self.json['sample_type'] == 'cancer':
                            if report_event.domain:
                                tier = int(report_event.domain[-1])
                        if variant_min_tier is None:
                            variant_min_tier = tier
                        elif tier < variant_min_tier:
                            variant_min_tier = tier
                    variant.max_tier = variant_min_tier

                    interesting_variant = False
                    if ig_obj.interpretationService == 'Exomiser':
                        for report_event in variant.reportEvents:
                            if report_event.score >= 0.95:
                                interesting_variant = False
                    elif ig_obj.interpretationService == 'genomics_england_tiering':
                        if not self.pullt3:
                            if variant.max_tier < 3:
                                interesting_variant = True
                        else:
                            interesting_variant = True
                    else:
                        interesting_variant = True  # CIP variants all get pulled

                    if interesting_variant:
                        variant_object_count += 1
                        case_variant = CaseVariant(
                            chromosome=variant.variantCoordinates.chromosome,
                            position=variant.variantCoordinates.position,
                            ref=variant.variantCoordinates.reference,
                            alt=variant.variantCoordinates.alternate,
                            case_id=self.request_id,
                            variant_count=str(variant_object_count),
                            genome_build=genome_build
                        )
                        case_variant_list.append(case_variant)
                        variant.case_variant = case_variant
                    else:
                        variant.case_variant = False
            self.ig_objs.append(ig_obj)
        for clinical_report in self.json['clinical_report']:
            cr_obj = ClinicalReport.fromJsonDict(clinical_report['clinical_report_data'])
            if cr_obj.variants:
                for variant in cr_obj.variants:
                    variant_min_tier = None
                    for report_event in variant.reportEvents:
                        if self.json['sample_type'] == 'raredisease':
                            if report_event.tier:
                                tier = int(report_event.tier[-1])
                        elif self.json['sample_type'] == 'cancer':
                            if report_event.domain:
                                tier = int(report_event.domain[-1])
                        if variant_min_tier is None:
                            variant_min_tier = tier
                        elif tier < variant_min_tier:
                            variant_min_tier = tier
                    variant.max_tier = variant_min_tier

                    variant_object_count += 1
                    case_variant = CaseVariant(
                        chromosome=variant.variantCoordinates.chromosome,
                        position=variant.variantCoordinates.position,
                        ref=variant.variantCoordinates.reference,
                        alt=variant.variantCoordinates.alternate,
                        case_id=self.request_id,
                        variant_count=str(variant_object_count),
                        genome_build=genome_build
                    )
                    case_variant_list.append(case_variant)
                    variant.case_variant = case_variant
            self.clinical_report_objs.append(cr_obj)

        return case_variant_list


class CaseAttributeManager(object):
    """
    Handler for managing each different type of case attribute.
    Holds get/refresh functions to be called by MCA, as well as pointing to
    CaseModels and ManyCaseModels for access by MCA.bulk_create_new().
    """
    def __init__(self, case, model_type, model_objects, many=False):
        """
        Initialise with CaseModel or ManyCaseModel, dependent on many param.
        """
        self.case = case  # for accessing related table entries
        self.model_type = model_type
        self.model_objects = model_objects
        self.many = many
        self.case_model = self.get_case_model()

    def get_case_model(self):
        """
        Call the corresponding function to update the case model within the
        AttributeManager.
        """

        if self.model_type == Clinician:
            case_model = self.get_clinician()
        elif self.model_type == Proband:
            case_model = self.get_proband()
        elif self.model_type == Family:
            case_model = self.get_family()
        elif self.model_type == Relative:
            case_model = self.get_relatives()
        elif self.model_type == Phenotype:
            case_model = self.get_phenotypes()
        elif self.model_type == FamilyPhenotype:
            case_model = self.get_family_phenotypes()
        elif self.model_type == InterpretationReportFamily:
            case_model = self.get_ir_family()
        elif self.model_type == Panel:
            case_model = self.get_panels()
        elif self.model_type == PanelVersion:
            case_model = self.get_panel_versions()
        elif self.model_type == InterpretationReportFamilyPanel:
            case_model = self.get_ir_family_panel()
        elif self.model_type == Gene:
            case_model = self.get_genes()
        elif self.model_type == PanelVersionGene:
            case_model = self.get_panel_version_genes()
        elif self.model_type == Transcript:
            case_model = self.get_transcripts()
        elif self.model_type == GELInterpretationReport:
            case_model = self.get_ir()
        elif self.model_type == Variant:
            case_model = self.get_variants()
        elif self.model_type == TranscriptVariant:
            case_model = self.get_transcript_variants()
        elif self.model_type == PVFlag:
            case_model = self.get_pv_flags()
        elif self.model_type == ProbandVariant:
            case_model = self.get_proband_variants()
        elif self.model_type == ProbandTranscriptVariant:
            case_model = self.get_proband_transcript_variants()
        elif self.model_type == ReportEvent:
            case_model = self.get_report_events()
        elif self.model_type == ToolOrAssemblyVersion:
            case_model = self.get_tool_and_assembly_versions()

        return case_model

    def get_clinician(self):
        """
        Create a case model to handle adding/getting the clinician for case.
        """
        # family ID used to search for clinician details in labkey
        family_id = None
        clinician_details = {"name": "unknown", "hospital": "unknown"}
        if self.case.json['sample_type'] == 'raredisease':
            family_id = self.case.json["family_id"]
            search_term = 'family_id'
        elif self.case.json['sample_type'] == 'cancer':
            family_id = self.case.json["proband"]
            search_term = 'participant_identifiers_id'
        # load in site specific details from config file
        if not self.case.skip_demographics:
            for row in self.case.clinicians:
                try:
                    if row[search_term] == family_id:
                        if row.get('consultant_details_full_name_of_responsible_consultant'):
                            clinician_details['name'] = row.get(
                                'consultant_details_full_name_of_responsible_consultant')
                except IndexError as e:
                    pass
        if self.case.ir_obj.workspace:
            clinician_details['hospital'] = self.case.ir_obj.workspace[0]
        else:
            clinician_details['hospital'] = 'unknown'
        clinician = CaseModel(Clinician, {
            "name": clinician_details['name'],
            "email": "unknown",  # clinician email not on labkey
            "hospital": clinician_details['hospital'],
            "added_by_user": False
        }, self.model_objects)
        return clinician

    def get_paricipant_demographics(self, participant_id):
        '''
        Calls labkey to retrieve participant demographics
        :param participant_id: GEL participant ID
        :return: dict containing participant demographics
        '''
        # load in site specific details from config file
        participant_demographics = {
            "surname": 'unknown',
            "forename": 'unknown',
            "date_of_birth": '2011/01/01',  # unknown but needs to be in date format
            "nhs_num": 'unknown',
        }

        if not self.case.skip_demographics:
            for row in self.case.demographics:
                try:
                    if row['participant_id'] == participant_id:
                        participant_demographics["surname"] = row.get(
                            'surname')
                        participant_demographics["forename"] = row.get(
                            'forenames')
                        participant_demographics["date_of_birth"] = row.get(
                            'date_of_birth').split(' ')[0]
                        if self.case.json['sample_type'] == 'raredisease':
                            if row.get('person_identifier_type').upper() == "NHSNUMBER":
                                participant_demographics["nhs_num"] = row.get(
                                    'person_identifier')
                        elif self.case.json['sample_type'] == 'cancer':
                            participant_demographics["nhs_num"] = row.get(
                                'person_identifier')
                except IndexError as e:
                    pass
        return participant_demographics

    def get_proband(self):
        """
        Create a case model to handle adding/getting the proband for case.
        """
        participant_id = self.case.json["proband"]

        demographics = self.get_paricipant_demographics(participant_id)
        family = self.case.attribute_managers[Family].case_model
        clinician = self.case.attribute_managers[Clinician].case_model
        recruiting_disease = None
        disease_subtype = None
        disease_group = None
        try:
            if self.case.json['sample_type'] == 'cancer':
                recruiting_disease = self.case.proband.primaryDiagnosisDisease[0]
                disease_subtype = self.case.proband.primaryDiagnosisSubDisease[0]
        except (TypeError, KeyError):
            pass

        if not self.case.skip_demographics:
            # set up LabKey to get recruited disease
            if self.case.json['sample_type'] == 'raredisease':
                for row in self.case.diagnosis:
                    try:
                        if row['participant_identifiers_id'] == participant_id:
                            disease_group = row.get('gel_disease_information_disease_group', None)
                            recruiting_disease = row.get('gel_disease_information_specific_disease', None)
                            disease_subtype = row.get('gel_disease_information_disease_subgroup', None)
                    except IndexError:
                        pass

        proband = CaseModel(Proband, {
            "gel_id": participant_id,
            "family": family.entry,
            "nhs_number": demographics['nhs_num'],
            "forename": demographics["forename"],
            "surname": demographics["surname"],
            "date_of_birth": datetime.strptime(demographics["date_of_birth"], "%Y/%m/%d").date(),
            "sex": self.case.proband.sex,
            "recruiting_disease": recruiting_disease,
            'disease_group': disease_group,
            'disease_subtype': disease_subtype,
            "gmc": clinician.entry.hospital
        }, self.model_objects)
        return proband

    def get_relatives(self):
        """
        Creates entries for each relative. Calls labkey to retrieve demograhics
        """
        family_members = self.case.family_members
        relative_list = []
        for family_member in family_members:
            demographics = self.get_paricipant_demographics(family_member['gel_id'])
            proband = self.case.attribute_managers[Proband].case_model
            if family_member['gel_id'] != 'None':
                relative = {
                    "gel_id": family_member['gel_id'],
                    "relation_to_proband": family_member["relation_to_proband"],
                    "affected_status": family_member["affection_status"],
                    "sequenced": family_member["sequenced"],
                    "proband": proband.entry,
                    "nhs_number": demographics["nhs_num"],
                    "forename": demographics["forename"],
                    "surname":demographics["surname"],
                    "date_of_birth": demographics["date_of_birth"],
                    "sex": family_member["sex"],
                }
                relative_list.append(relative)
        relatives = ManyCaseModel(Relative, [{
            "gel_id": relative['gel_id'],
            "relation_to_proband": relative["relation_to_proband"],
            "affected_status": relative["affected_status"],
            "proband": relative['proband'],
            "sequenced": relative['sequenced'],
            "nhs_number": relative["nhs_number"],
            "forename": relative["forename"],
            "surname": relative["surname"],
            "date_of_birth": datetime.strptime(relative["date_of_birth"], "%Y/%m/%d").date(),
            "sex": relative["sex"],
        } for relative in relative_list], self.model_objects)

        return relatives

    def get_family(self):
        """
        Create case model to handle adding/getting family for this case.
        """
        family_members = self.case.family_members
        self.case.mother = {}
        self.case.father = {}
        self.case.mother['sequenced'] = False
        self.case.father['sequenced'] = False

        for family_member in family_members:
            if family_member["relation_to_proband"] == "Father":
                self.case.father = family_member
            elif family_member["relation_to_proband"] == "Mother":
                self.case.mother = family_member

        self.case.trio_sequenced = False

        if self.case.mother["sequenced"] and self.case.father["sequenced"]:
            # participant has a mother and father recorded
            self.case.trio_sequenced = True

        self.case.has_de_novo = False
        if self.case.trio_sequenced:
            # determine if any de_novo variants present
            variants_to_check = []

            # standard tiered variants
            for ig in self.case.json['interpreted_genome']:
                ig_obj = InterpretedGenome.fromJsonDict(ig['interpreted_genome_data'])
                if ig_obj.variants:
                    for variant in ig_obj.variants:
                        variant.maternal_zygosity = 'unknown'
                        variant.paternal_zygosity = 'unknown'
                        for call in variant.variantCalls:
                            if call.participantId == self.case.mother["gel_id"]:
                                variant.maternal_zygosity = call.zygosity
                            elif call.participantId == self.case.father["gel_id"]:
                                variant.paternal_zygosity = call.zygosity
                        variants_to_check.append(variant)

            for clinical_report in self.case.json['clinical_report']:
                cr_obj = ClinicalReport.fromJsonDict(clinical_report['clinical_report_data'])
                if cr_obj.variants:
                    for variant in cr_obj.variants:
                        variant.maternal_zygosity = 'unknown'
                        variant.paternal_zygosity = 'unknown'
                        for call in variant.variantCalls:
                            if call.participantId == self.case.mother["gel_id"]:
                                variant.maternal_zygosity = call.zygosity
                            elif call.participantId == self.case.father["gel_id"]:
                                variant.paternal_zygosity = call.zygosity
                        variants_to_check.append(variant)

            for variant in variants_to_check:
                inheritance = self.determine_variant_inheritance(variant)
                if inheritance == "de_novo":
                    self.case.has_de_novo = True
                    # found a de novo, can stop here
                    break

        clinician = self.case.attribute_managers[Clinician].case_model
        if self.case.json['sample_type'] == 'raredisease':
            family_id = self.case.json["family_id"]
        elif self.case.json['sample_type'] == 'cancer':
            family_id = self.case.json["proband"]
        family = CaseModel(Family, {
            "clinician": clinician.entry,
            "gel_family_id": family_id,
            "trio_sequenced": self.case.trio_sequenced,
            "has_de_novo": self.case.has_de_novo
        }, self.model_objects)
        return family

    def get_phenotypes(self):
        """
        Create a list of CaseModels for phenotypes for this case.
        """
        if self.case.json['sample_type'] == 'raredisease':
            phenotypes = ManyCaseModel(Phenotype, [
                {"hpo_terms": phenotype.term,
                 "description": "unknown"}
                for phenotype in self.case.proband.hpoTermList
                if phenotype.termPresence == 'yes'
            ], self.model_objects)
        else:
            phenotypes = ManyCaseModel(Phenotype, [], self.model_objects)
        return phenotypes

    def get_family_phenotyes(self):
        # TODO
        family_phenotypes = ManyCaseModel(FamilyPhenotype, [
            {"family": None,
             "phenotype": None}
        ], self.model_objects)

        return family_phenotypes

    def get_panelapp_api_response(self, panel, panel_file):
        panelapp_poll = PollAPI(
            "panelapp", f"get_panel/{panel.panelName}/?version={panel.panelVersion}")
        with open(panel_file, 'w') as f:
            json.dump(panelapp_poll.get_json_response(), f)
            panel_app_response = panelapp_poll.get_json_response()

        return panel_app_response

    def get_panels(self):
        """
        Poll panelApp to fetch information about a panel, then create a
        ManyCaseModel with this information.
        """
        config_dict = load_config.LoadConfig().load()
        panelapp_storage = config_dict['panelapp_storage']
        if self.case.panels:
            for panel in self.case.panels:
                polled = self.case.panel_manager.fetch_panel_response(
                    panelapp_id=panel.panelName,
                    panel_version=panel.panelVersion
                )
                if polled:
                    panel.panelapp_results = polled.results
                if not polled:
                    panel_file = os.path.join(panelapp_storage, f'{panel.panelName}_{panel.panelVersion}.json')
                    if os.path.isfile(panel_file):

                        try:
                            panelapp_response = json.load(open(panel_file))
                        except:
                            panelapp_response = self.get_panelapp_api_response(panel, panel_file)
                    else:
                        panelapp_response = self.get_panelapp_api_response(panel, panel_file)

                    # inform the PanelManager that a new panel has been added
                    polled = self.case.panel_manager.add_panel_response(
                        panelapp_id=panel.panelName,
                        panel_version=panel.panelVersion,
                        panelapp_response=panelapp_response["result"]
                    )
                    panel.panelapp_results = polled.results

            for panel in self.case.panels:
                panel.panel_name_results = self.case.panel_manager.fetch_panel_names(
                    panelapp_id=panel.panelName
                )

            panels = ManyCaseModel(Panel, [{
                "panelapp_id": panel.panelName,
                "panel_name": panel.panel_name_results["SpecificDiseaseName"],
                "disease_group": panel.panel_name_results["DiseaseGroup"],
                "disease_subgroup": panel.panel_name_results["DiseaseSubGroup"]
            } for panel in self.case.panels], self.model_objects)
        else:
            panels = ManyCaseModel(Panel, [], self.model_objects)

        return panels

    def get_panel_versions(self):
        """
        Add the panel model to description in case.panel then set values
        for the ManyCaseModel.
        """
        panel_models = [
            # get all the panel models from the attribute manager
            case_model.entry
            for case_model
            in self.case.attribute_managers[Panel].case_model.case_models]
        if self.case.panels:
            for panel in self.case.panels:
                # set self.case.panels["model"] to the correct model
                for panel_model in panel_models:
                    if panel.panelName == panel_model.panelapp_id:
                        panel.model = panel_model

            panel_versions = ManyCaseModel(PanelVersion, [{
                # create the MCM
                "version_number": panel.panelapp_results["version"],
                "panel": panel.model
            } for panel in self.case.panels], self.model_objects)
        else:
            panel_versions = ManyCaseModel(PanelVersion, [], self.model_objects)
        return panel_versions

    def get_genes(self):
        """
        Create gene objects from the genes from panelapp.
        """
        panels = self.case.panels

        # get the list of genes from the panelapp_result
        gene_list = []
        if panels:
            for panel in panels:
                genes = panel.panelapp_results["Genes"]
                gene_list += genes

        for gene in gene_list:
            # Alot of pilot cases just have E for this
            if not gene["EnsembleGeneIds"] or gene["EnsembleGeneIds"] == 'E':
                gene["EnsembleGeneIds"] = None
            else:
                if type(gene['EnsembleGeneIds']) is str:
                    gene['EnsembleGeneIds'] = gene['EnsembleGeneIds']
                else:
                    gene['EnsembleGeneIds'] = gene['EnsembleGeneIds'][0]

        self.case.gene_manager.load_genes()

        for transcript in self.case.transcripts:
            if transcript.gene_ensembl_id and transcript.gene_hgnc_id:
                gene_list.append({
                    'EnsembleGeneIds': transcript.gene_ensembl_id,
                    'GeneSymbol': transcript.gene_hgnc_name,
                    'HGNC_ID': str(transcript.gene_hgnc_id),
                })
                self.case.gene_manager.add_searched(transcript.gene_ensembl_id, str(transcript.gene_hgnc_id))

        for gene in tqdm(gene_list, desc=self.case.request_id):
            gene['HGNC_ID'] = None
            if gene['EnsembleGeneIds']:
                # tqdm.write(gene["EnsembleGeneIds"])
                polled = self.case.gene_manager.fetch_searched(gene['EnsembleGeneIds'])
                if polled == 'Not_found':
                    gene['HGNC_ID'] = None
                elif not polled:
                    genename_poll = PollAPI(
                        "genenames", "search/{gene}/".format(
                            gene=gene["EnsembleGeneIds"])
                    )
                    genename_response = genename_poll.get_json_response()
                    if genename_response['response']['docs']:
                        hgnc_id = genename_response['response']['docs'][0]['hgnc_id'].split(':')
                        gene['HGNC_ID'] = str(hgnc_id[1])
                        self.case.gene_manager.add_searched(gene["EnsembleGeneIds"], str(hgnc_id[1]))
                    else:
                        self.case.gene_manager.add_searched(gene["EnsembleGeneIds"], 'Not_found')
                else:
                    gene['HGNC_ID'] = polled

        cleaned_gene_list = []
        for gene in gene_list:
            if gene['HGNC_ID']:
                self.case.gene_manager.add_gene(gene)
                new_gene = self.case.gene_manager.fetch_gene(gene)
                cleaned_gene_list.append(new_gene)

        self.case.gene_manager.write_genes()

        genes = ManyCaseModel(Gene, [{
            "ensembl_id": gene["EnsembleGeneIds"],  # TODO: which ID to use?
            "hgnc_name": gene["GeneSymbol"],
            "hgnc_id": gene['HGNC_ID']
        } for gene in cleaned_gene_list if gene["HGNC_ID"]], self.model_objects)
        return genes

    def get_panel_version_genes(self):
        # TODO: implement M2M relationship
        panel_version_genes = ManyCaseModel(PanelVersionGenes, [{
            "panel_version": None,
            "gene": None
        }], self.model_objects)

        return panel_version_genes

    def get_transcripts(self):
        """
        Create a ManyCaseModel for transcripts based on information returned
        from VEP.
        """
        tool_models = [
            case_model.entry
            for case_model in self.case.attribute_managers[ToolOrAssemblyVersion].case_model.case_models]

        genome_assembly = None

        for tool in tool_models:
            if tool.tool_name == 'genome_build':
                genome_assembly = tool

        genes = self.case.attribute_managers[Gene].case_model.case_models
        case_transcripts = self.case.transcripts
        # for each transcript, add an FK to the gene with matching ensg ID
        for transcript in case_transcripts:
            # convert canonical to bools:
            transcript.canonical = transcript.transcript_canonical == "YES"
            if self.case.json['sample_type'] == 'cancer':
                transcript.selected = transcript.transcript_canonical == "YES"
            if not transcript.gene_hgnc_id:
                # if the transcript has no recognised gene associated
                continue  # don't bother checking genes
            transcript.gene_model = None
            for gene in genes:
                if gene.entry.hgnc_id == transcript.gene_hgnc_id:
                    transcript.gene_model = gene.entry
                    if self.case.json['sample_type'] == 'raredisease':
                        preferred_transcript = PreferredTranscript.objects.filter(gene=gene.entry,
                                                                                  genome_assembly=genome_assembly)
                        if preferred_transcript:
                            preferred_transcript = preferred_transcript.first()
                            if preferred_transcript.transcript.name == transcript.transcript_name:
                                transcript.selected = True
                        else:
                            transcript.selected = transcript.transcript_canonical == "YES"

        transcripts = ManyCaseModel(Transcript, [{
            "gene": transcript.gene_model,
            "name": transcript.transcript_name,
            "canonical_transcript": transcript.canonical,
            "strand": transcript.transcript_strand,
            'genome_assembly': genome_assembly
            # add all transcripts except those without associated genes
        } for transcript in case_transcripts if transcript.gene_model], self.model_objects)

        return transcripts

    def get_ir_family(self):
        """
        Create a CaseModel for the new IRFamily Model to be added to the
        database (unlike before it is impossible that this alreay exists).
        """
        family = self.case.attribute_managers[Family].case_model
        ir_family = CaseModel(InterpretationReportFamily, {
            "participant_family": family.entry,
            "cip": self.case.json["cip"],
            "ir_family_id": self.case.request_id,
            "priority": self.case.json["case_priority"]
        }, self.model_objects)
        return ir_family

    def get_ir_family_panel(self):
        """
        Through table linking panels to IRF when no variants have been reported
        within a particular panel for a case.
        """
        # get the string names of all genes which fall below 95% 15x coverage
        genes_failing_coverage = []
        for panel in self.case.attribute_managers[PanelVersion].case_model.case_models:
            if "entry" in vars(panel):
                if self.case.ir_obj.genePanelsCoverage:
                    panel_coverage = self.case.ir_obj.genePanelsCoverage.get(panel.entry.panel.panelapp_id, {})
                    for gene, coverage_dict in panel_coverage.items():
                        if float(coverage_dict["_".join((self.case.proband_sample, "gte15x"))]) < 0.95:
                            genes_failing_coverage.append(gene)

        genes_failing_coverage = sorted(set(genes_failing_coverage))
        if 'SUMMARY' in genes_failing_coverage: 
            genes_failing_coverage.remove('SUMMARY')
        str_genes_failing_coverage = ''
        for gene in genes_failing_coverage:
            str_genes_failing_coverage += gene + ', '
        str_genes_failing_coverage = str_genes_failing_coverage[:-2]
        str_genes_failing_coverage += '.'

        ir_family = self.case.attribute_managers[InterpretationReportFamily].case_model

        if self.case.ir_obj.genePanelsCoverage:
            ir_family_panels = ManyCaseModel(InterpretationReportFamilyPanel, [{
                "ir_family": ir_family.entry,
                "panel": panel.entry,
                "custom": False,
                "average_coverage": self.case.ir_obj.genePanelsCoverage[panel.entry.panel.panelapp_id]["SUMMARY"].get("_".join((self.case.proband_sample, "avg")), None),
                "proportion_above_15x": self.case.ir_obj.genePanelsCoverage[panel.entry.panel.panelapp_id]["SUMMARY"].get("_".join((self.case.proband_sample, "gte15x")), None),
                "genes_failing_coverage": str_genes_failing_coverage
            } for panel in self.case.attribute_managers[PanelVersion].case_model.case_models if "entry" in vars(panel) and
                panel.entry.panel.panelapp_id in self.case.ir_obj.genePanelsCoverage and
                'SUMMARY' in self.case.ir_obj.genePanelsCoverage[panel.entry.panel.panelapp_id]],
                self.model_objects)
        else:
            ir_family_panels = ManyCaseModel(InterpretationReportFamilyPanel, [], self.model_objects)

        return ir_family_panels

    def get_ir(self):
        """
        Get json information about an Interpretation Report and create a
        CaseModel from it.
        """
        case_attribute_managers = self.case.attribute_managers
        irf_manager = case_attribute_managers[InterpretationReportFamily]
        ir_family = irf_manager.case_model

        # find assembly
        tool_models = [
            case_model.entry
            for case_model in self.case.attribute_managers[ToolOrAssemblyVersion].case_model.case_models]
        genome_assembly = None
        for tool in tool_models:
            if tool.tool_name == 'genome_build':
                genome_assembly = tool

        # find the max tier
        self.case.processed_variants = self.process_proband_variants()
        self.case.max_tier = 3
        for variant in self.case.processed_variants:
            if variant['max_tier']:
                if variant['max_tier'] < self.case.max_tier:
                    self.case.max_tier = variant['max_tier']

        tumour_content = None
        if self.case.json['sample_type'] == 'cancer':
            tumour_content = self.case.proband.tumourSamples[0].tumourContent
        has_germline_variant = False
        if self.case.json['sample_type'] == 'cancer':
            for ig_obj in self.case.ig_objs:
                alleleorigins = [variant.variantAttributes.alleleOrigins[0] for variant in ig_obj.variants]
                if "germline_variant" in alleleorigins:
                    has_germline_variant = True

        ir = CaseModel(GELInterpretationReport, {
            "ir_family": ir_family.entry,
            "polled_at_datetime": timezone.now(),
            "sha_hash": self.case.json_hash,
            "status": self.case.status["status"],
            "updated": timezone.make_aware(
                datetime.strptime(
                    self.case.status["created_at"][:19],
                    '%Y-%m-%dT%H:%M:%S'
                )),
            "user": self.case.status["user"],
            "max_tier": self.case.max_tier,
            "assembly": genome_assembly,
            'sample_type': self.case.json['sample_type'],
            "sample_id": self.case.proband_sample,
            'tumour_content': tumour_content,
            "has_germline_variant": has_germline_variant,
            "case_status": 'N',  # initialised to not started? (N)
        }, self.model_objects)
        return ir

    def get_variants(self):
        """
        Get the variant information (genetic position) for the variants in this
        case and return a matching ManyCaseModel with model_type = Variant.
        """
        tool_models = [
            case_model.entry
            for case_model in self.case.attribute_managers[ToolOrAssemblyVersion].case_model.case_models]

        genome_assembly = None

        for tool in tool_models:
            if tool.tool_name == 'genome_build':
                genome_assembly = tool

        variants_list = []
        # loop through all variants and check that they have a case_variant
        for ig_obj in self.case.ig_objs:
            if ig_obj.variants:
                for variant in ig_obj.variants:
                    if variant.case_variant:
                        variant.dbsnp = None
                        if variant.variantAttributes.variantIdentifiers.dbSnpId:
                            if re.match('rs\d+', variant.variantAttributes.variantIdentifiers.dbSnpId):
                                variant.dbsnp = variant.variantAttributes.variantIdentifiers.dbSnpId
                        tiered_variant = {
                            "genome_assembly": genome_assembly,
                            "alternate": variant.case_variant.alt,
                            "chromosome": variant.case_variant.chromosome,
                            "db_snp_id": variant.dbsnp,
                            "reference": variant.case_variant.ref,
                            "position": variant.case_variant.position,
                        }
                        variants_list.append(tiered_variant)

        for clinical_report in self.case.clinical_report_objs:
            if clinical_report.variants:
                for variant in clinical_report.variants:
                    variant.dbsnp = None
                    if variant.variantAttributes.variantIdentifiers.dbSnpId:
                        if re.match('rs\d+', variant.variantAttributes.variantIdentifiers.dbSnpId):
                            variant.dbsnp = variant.variantAttributes.variantIdentifiers.dbSnpId
                    cip_variant = {
                        "genome_assembly": genome_assembly,
                        "alternate": variant.case_variant.alt,
                        "chromosome": variant.case_variant.chromosome,
                        "db_snp_id": variant.dbsnp,
                        "reference": variant.case_variant.ref,
                        "position": variant.case_variant.position,
                    }
                    variants_list.append(cip_variant)

        for variant in variants_list:
            self.case.variant_manager.add_variant(variant)

        cleaned_variant_list = []
        for variant in variants_list:
            cleaned_variant_list.append(self.case.variant_manager.fetch_variant(variant))

        # set and return the MCM
        variants = ManyCaseModel(Variant, [{
            "genome_assembly": genome_assembly,
            "alternate": variant["alternate"],
            "chromosome": variant["chromosome"],
            "db_snp_id": variant["db_snp_id"],
            "reference": variant["reference"],
            "position": variant["position"],
        } for variant in cleaned_variant_list], self.model_objects)

        return variants

    def get_transcript_variants(self):
        """
        Get all variant transcripts. This is essentialy a 'through' table for
        the M2M relationship between Variant and Transcript, but with extra
        information.
        """
        # get all Transcript and Variant entries
        tool_models = [
            case_model.entry
            for case_model in self.case.attribute_managers[ToolOrAssemblyVersion].case_model.case_models]

        genome_assembly = None

        for tool in tool_models:
            if tool.tool_name == 'genome_build':
                genome_assembly = tool

        case_attribute_managers = self.case.attribute_managers
        transcript_manager = case_attribute_managers[Transcript].case_model
        transcript_entries = [transcript.entry
                              for transcript in transcript_manager.case_models]
        variant_manager = case_attribute_managers[Variant].case_model
        variant_entries = [variant.entry
                           for variant in variant_manager.case_models]

        # for each CaseTranscript (which contains necessary info):
        for case_transcript in self.case.transcripts:
            # get information to hook up transcripts with variants
            case_id = case_transcript.case_id
            variant_id = case_transcript.variant_count
            for variant in self.case.variants:
                if (
                    case_id == variant.case_id and
                    variant_id == variant.variant_count
                ):
                    case_variant = variant
                    break

            # name to hook up CaseTranscript with Transcript
            transcript_name = case_transcript.transcript_name

            # add the corresponding Variant entry
            for variant_entry in variant_entries:
                # find the matching variant entry
                if (
                    variant_entry.chromosome == case_variant.chromosome and
                    variant_entry.position == case_variant.position and
                    variant_entry.reference == case_variant.ref and
                    variant_entry.alternate == case_variant.alt
                ):
                    # add match to the case_transcript
                    case_transcript.variant_entry = variant_entry

            # add the corresponding Transcript entry
            for transcript_entry in transcript_entries:
                found = False
                if transcript_entry.name == transcript_name and transcript_entry.genome_assembly == genome_assembly:
                    case_transcript.transcript_entry = transcript_entry
                    found = True
                    break
                if not found:
                    # we don't make entries for tx with no Gene
                    case_transcript.transcript_entry = None

        # use the updated CaseTranscript instances to create an MCM
        transcript_variants = ManyCaseModel(TranscriptVariant, [{
            "transcript": transcript.transcript_entry,
            "variant": transcript.variant_entry,
            "af_max": transcript.transcript_variant_af_max,
            "hgvs_c": transcript.transcript_variant_hgvs_c,
            "hgvs_p": transcript.transcript_variant_hgvs_p,
            "hgvs_g": transcript.transcript_variant_hgvs_g,
            "sift": transcript.variant_sift,
            "polyphen": transcript.variant_polyphen,
        } for transcript in self.case.transcripts
            if transcript.transcript_entry], self.model_objects)

        return transcript_variants

    def process_proband_variants(self):
        """
        Take all proband variants from this case and process them for
        get_proband_variants.
        """
        proband_manager = self.case.attribute_managers[Proband]

        variant_entries = [
            variant.entry
            for variant
            in self.case.attribute_managers[Variant].case_model.case_models
        ]
        raw_proband_variants = []
        processed_proband_variants = []
        for ig_obj in self.case.ig_objs:
            if ig_obj.variants:
                for ig_variant in ig_obj.variants:
                    if ig_variant.case_variant:
                        raw_proband_variants.append(ig_variant)
        for clinical_report in self.case.clinical_report_objs:
            if clinical_report.variants:
                for variant in clinical_report.variants:
                    raw_proband_variants.append(variant)

        for ig_variant in raw_proband_variants:
            # some json_variants won't have an entry (T3), so:
            ig_variant.somatic = False
            ig_variant.variant_entry = None
            # for those that do, fetch from list of entries:
            # variant in json matches variant entry
            for variant in variant_entries:
                if (
                        ig_variant.variantCoordinates.chromosome == variant.chromosome and
                        ig_variant.variantCoordinates.position == variant.position and
                        ig_variant.variantCoordinates.reference == variant.reference and
                        ig_variant.variantCoordinates.alternate == variant.alternate
                ):
                    # variant in json matches variant entry
                    ig_variant.variant_entry = variant
                ig_variant.zygosity = 'unknown'
                ig_variant.maternal_zygosity = 'unknown'
                ig_variant.paternal_zygosity = 'unknown'

                for call in ig_variant.variantCalls:
                    if call.participantId == proband_manager.case_model.entry.gel_id:
                        if call.zygosity != 'na':
                            ig_variant.zygosity = call.zygosity
                    elif call.participantId == self.case.mother.get("gel_id", None):
                        if call.zygosity != 'na':
                            ig_variant.maternal_zygosity = call.zygosity
                    elif call.participantId == self.case.father.get("gel_id", None):
                        if call.zygosity != 'na':
                            ig_variant.paternal_zygosity = call.zygosity

                    if call:
                        if ig_variant.variantAttributes.alleleOrigins[0] == 'somatic_variant':
                            ig_variant.somatic = True

        for ig_variant in raw_proband_variants:
            proband_variant = {
                "max_tier": ig_variant.max_tier,
                "variant": ig_variant.variant_entry,
                "zygosity": ig_variant.zygosity,
                "maternal_zygosity": ig_variant.maternal_zygosity,
                "paternal_zygosity": ig_variant.paternal_zygosity,
                "somatic": ig_variant.somatic,
                'variant_obj': ig_variant
            }
            processed_proband_variants.append(proband_variant)

        # remove duplicate variants
        uniq_proband_variants = []
        seen_variants = []

        for variant in processed_proband_variants:
            if variant['variant'] not in seen_variants:
                uniq_proband_variants.append(variant)
                seen_variants.append(variant['variant'])

        return uniq_proband_variants

    def get_proband_variants(self):
        """
        Get proband variant information from VEP and the JSON and create MCM.
        """

        ir_manager = self.case.attribute_managers[GELInterpretationReport]

        tiered_and_cip_proband_variants = self.case.processed_variants

        proband_variants = ManyCaseModel(ProbandVariant, [{
            "interpretation_report": ir_manager.case_model.entry,
            "max_tier": variant['max_tier'],
            "variant": variant["variant"],
            "zygosity": variant["zygosity"],
            "maternal_zygosity": variant['maternal_zygosity'],
            "paternal_zygosity": variant['paternal_zygosity'],
            "inheritance": self.determine_variant_inheritance(variant['variant_obj']),
            "somatic": variant["somatic"]
        } for variant in tiered_and_cip_proband_variants], self.model_objects)

        return proband_variants

    def determine_variant_inheritance(self, variant):
        """
        Take a variant, and use maternal and paternal zygosities to determine
        inheritance.
        """

        if variant.maternal_zygosity == 'reference_homozygous' and variant.paternal_zygosity == 'reference_homozygous':
            # neither parent has variant, --/-- cross so must be de novo
            inheritance = 'de_novo'

        elif "heterozygous" in variant.maternal_zygosity or "heterozygous" in variant.paternal_zygosity:
            # catch +-/?? cross
            inheritance = 'inherited'

        elif "alternate" in variant.maternal_zygosity or "alternate" in variant.paternal_zygosity:
            # catch ++/?? cross
            inheritance = 'inherited'

        else:
            # cannot determine
            inheritance = 'unknown'

        # print("Proband I:", inheritance)
        return inheritance

    def get_pv_flags(self):
        proband_variants = [proband_variant.entry for proband_variant
                            in self.case.attribute_managers[ProbandVariant].case_model.case_models]
        pv_flags = []
        for interpreted_genome in self.case.ig_objs:
            if interpreted_genome.variants:
                for variant in interpreted_genome.variants:
                    if variant.case_variant:
                        for proband_variant in proband_variants:
                            if proband_variant.variant == variant.variant_entry:
                                variant.proband_variant = proband_variant
                                variant.company = interpreted_genome.interpretationService
                                pv_flags.append(variant)
                                break

        for clinical_report in self.case.clinical_report_objs:
            if clinical_report.variants:
                for variant in clinical_report.variants:
                    for proband_variant in proband_variants:
                        if proband_variant.variant == variant.variant_entry:
                            variant.proband_variant = proband_variant
                            variant.company = 'Clinical Report'
                            pv_flags.append(variant)
                            break

        pv_flags = ManyCaseModel(PVFlag, [{
            "proband_variant": variant.proband_variant,
            'flag_name': variant.company
        } for variant in pv_flags], self.model_objects)

        return pv_flags

    def get_proband_transcript_variants(self):
        """
        Get the ProbandTranscriptVariants associated with this case and return
        a MCM containing them.
        """
        # associat a proband_variant with a transcript
        proband_variants = [proband_variant.entry for proband_variant
                            in self.case.attribute_managers[ProbandVariant].case_model.case_models]

        for transcript in self.case.transcripts:
            for proband_variant in proband_variants:
                if proband_variant.variant == transcript.variant_entry:
                    transcript.proband_variant_entry = proband_variant

        if self.case.json['sample_type'] == 'cancer':
            for transcript in self.case.transcripts:
                if transcript.transcript_entry:
                    for ig_obj in self.case.ig_objs:
                        if ig_obj.variants:
                            for variant in ig_obj.variants:
                                if variant.case_variant:
                                    if variant.variant_entry == transcript.variant_entry:
                                        for reportevent in variant.reportEvents:
                                            for en in reportevent.genomicEntities:
                                                if transcript.transcript_name == en.ensemblId:
                                                    transcript.selected = True
                                                else:
                                                    transcript.selected = False

        proband_transcript_variants = ManyCaseModel(ProbandTranscriptVariant, [{
            "transcript": transcript.transcript_entry,
            "proband_variant": transcript.proband_variant_entry,
            # default is true if assoc. tx is canonical
            "selected": transcript.selected,
            "effect": transcript.proband_transcript_variant_effect
        } for transcript
            in self.case.transcripts
            if transcript.transcript_entry
            and transcript.proband_variant_entry], self.model_objects)

        return proband_transcript_variants

    def get_tool_and_assembly_versions(self):
        '''
        Create tool and assembly entries for the case
        '''
        tools_and_assemblies = ManyCaseModel(ToolOrAssemblyVersion, [{
            "tool_name": tool,
            "version_number": version
        }for tool, version in self.case.tools_and_versions.items()], self.model_objects)

        return tools_and_assemblies


class CaseModel(object):
    """
    A handler for an instance of a model that belongs to a case. Holds an
    instance of a model (pre-creation or post-creation) and whether it
    requires creation in the database.
    """
    def __init__(self, model_type, model_attributes, model_objects):
        self.model_type = model_type

        self.model_attributes = model_attributes.copy()
        self.escaped_model_attributes = model_attributes.copy()
        self.string_escape_model_attributes()  # prevent sql injection

        self.model_objects = model_objects
        self.entry = self.check_found_in_db(self.model_objects)

    def string_escape_model_attributes(self):
        # string escape ' characters in model attributes for use with raw sql
        for k, v in self.escaped_model_attributes.items():
            if isinstance(self.escaped_model_attributes[k], str):
                self.escaped_model_attributes[k] = self.escaped_model_attributes[k].replace(
                    "'", "''"  # psql takes '' when ' is used in string to avoid term
                )

    def set_sql_cmd(self):
        # set raw sql to run against database to fetch matching record
        if self.model_type == Clinician:
            if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
                table = 'SELECT * FROM Clinician'
                cmd = ''.join([
                    " WHERE BINARY name = '{name}'",
                    " AND BINARY hospital = '{hospital}'",
                    " AND BINARY email = '{email}'"
                ]).format(
                    name=self.escaped_model_attributes["name"],
                    hospital=self.escaped_model_attributes["hospital"],
                    email=self.escaped_model_attributes["email"]
                )
            else:
                table = 'SELECT * FROM "Clinician"'
                cmd = ''.join([
                    " WHERE name = '{name}'",
                    " AND hospital = '{hospital}'",
                    " AND email = '{email}'"
                ]).format(
                    name=self.escaped_model_attributes["name"],
                    hospital=self.escaped_model_attributes["hospital"],
                    email=self.escaped_model_attributes["email"]
                )
        elif self.model_type == Proband:
            if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
                table = 'SELECT * FROM Proband'
            else:
                table = 'SELECT * FROM "Proband"'
            cmd = ''.join([
                " WHERE gel_id = '{gel_id}'"
            ]).format(
                gel_id=self.escaped_model_attributes["gel_id"]
            )
        elif self.model_type == Family:
            if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
                table = 'SELECT * FROM Family'
            else:
                table = 'SELECT * FROM "Family"'
            cmd = ''.join([
                " WHERE gel_family_id = '{gel_family_id}'"
            ]).format(
                gel_family_id=self.escaped_model_attributes["gel_family_id"]
            )
        elif self.model_type == Relative:
            if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
                table = 'SELECT * FROM Relative'
            else:
                table = 'SELECT * FROM "Relative"'
            cmd = ''.join([
                " WHERE gel_id = '{gel_id}'",
                " AND proband_id = {proband_id}"
            ]).format(
                gel_id=self.escaped_model_attributes["gel_id"],
                proband_id=self.escaped_model_attributes["proband"].id
            )
        elif self.model_type == Phenotype:
            if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
                table = 'SELECT * FROM Phenotype'
            else:
                table = 'SELECT * FROM "Phenotype"'
            cmd = ''.join([
                " WHERE hpo_terms = '{hpo_terms}'"
            ]).format(
                hpo_terms=self.escaped_model_attributes["hpo_terms"]
            )
        elif self.model_type == InterpretationReportFamily:
            if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
                table = 'SELECT * FROM InterpretationReportFamily'
            else:
                table = 'SELECT * FROM "InterpretationReportFamily"'
            cmd = ''.join([
                " WHERE ir_family_id = '{ir_family_id}'",
            ]).format(
                ir_family_id=self.escaped_model_attributes["ir_family_id"]
            )
        elif self.model_type == Panel:
            if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
                table = 'SELECT * FROM Panel'
            else:
                table = 'SELECT * FROM "Panel"'
            cmd = ''.join([
                " WHERE panelapp_id = '{panelapp_id}'",
            ]).format(
                panelapp_id=self.escaped_model_attributes["panelapp_id"]
            )
        elif self.model_type == PanelVersion:
            if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
                table = 'SELECT * FROM PanelVersion'
            else:
                table = 'SELECT * FROM "PanelVersion"'
            cmd = ''.join([
                " WHERE panel_id = '{panel_id}'",
                " AND version_number = '{version_number}'"
            ]).format(
                panel_id=self.escaped_model_attributes["panel"].id,
                version_number=self.escaped_model_attributes["version_number"]
            )
        elif self.model_type == InterpretationReportFamilyPanel:
            if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
                table = 'SELECT * FROM gel2mdt_interpretationreportfamilypanel'
            else:
                table = 'SELECT * FROM "gel2mdt_interpretationreportfamilypanel"'
            cmd = ''.join([
                " WHERE ir_family_id = {ir_family_id}",  # no ' because FKID
                " AND panel_id = {panel_id}"
            ]).format(
                ir_family_id=self.escaped_model_attributes["ir_family"].id,
                panel_id=self.escaped_model_attributes["panel"].id
            )
        elif self.model_type == Gene:
            if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
                table = 'SELECT * FROM Gene'
            else:
                table = 'SELECT * FROM "Gene"'
            cmd = ''.join([
                " WHERE hgnc_id = '{hgnc_id}'",
            ]).format(
                hgnc_id=self.escaped_model_attributes["hgnc_id"]
            )
        elif self.model_type == Transcript:
            if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
                table = 'SELECT * FROM Transcript'
            else:
                table = 'SELECT * FROM "Transcript"'
            cmd = ''.join([
                " WHERE name = '{name}'",
                " AND genome_assembly_id = {genome_assembly_id}"
            ]).format(
                name=self.escaped_model_attributes["name"],
                genome_assembly_id=self.escaped_model_attributes["genome_assembly"].id
            )
        elif self.model_type == GELInterpretationReport:
            if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
                table = 'SELECT * FROM GELInterpretationReport'
            else:
                table = 'SELECT * FROM "GELInterpretationReport"'
            cmd = ''.join([
                " WHERE sha_hash = '{sha_hash}'",
            ]).format(
                sha_hash=self.escaped_model_attributes["sha_hash"]
            )
        elif self.model_type == Variant:
            if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
                table = 'SELECT * FROM Variant'
            else:
                table = 'SELECT * FROM "Variant"'
            cmd = ''.join([
                " WHERE chromosome = '{chromosome}'",
                " AND position = {position}"
                " AND reference = '{reference}'"
                " AND alternate = '{alternate}'"
                " AND genome_assembly_id = {genome_assembly_id}"
            ]).format(
                chromosome=self.escaped_model_attributes["chromosome"],
                position=self.escaped_model_attributes["position"],
                reference=self.escaped_model_attributes["reference"],
                alternate=self.escaped_model_attributes["alternate"],
                genome_assembly_id=self.escaped_model_attributes["genome_assembly"].id
            )
        elif self.model_type == TranscriptVariant:
            if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
                table = 'SELECT * FROM TranscriptVariant'
            else:
                table = 'SELECT * FROM "TranscriptVariant"'
            cmd = ''.join([
                " WHERE transcript_id = {transcript_id}",
                " AND variant_id = {variant_id}"
            ]).format(
                transcript_id=self.escaped_model_attributes["transcript"].id,
                variant_id=self.escaped_model_attributes["variant"].id
            )
        elif self.model_type == ProbandVariant:
            if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
                table = 'SELECT * FROM ProbandVariant'
            else:
                table = 'SELECT * FROM "ProbandVariant"'
            cmd = ''.join([
                " WHERE variant_id = {variant_id}",
                " AND interpretation_report_id = {interpretation_report_id}"
            ]).format(
                variant_id=self.escaped_model_attributes["variant"].id,
                interpretation_report_id=self.escaped_model_attributes["interpretation_report"].id
            )
        elif self.model_type == PVFlag:
            if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
                table = 'SELECT * FROM PVFlag'
            else:
                table = 'SELECT * FROM "PVFlag"'
            cmd = ''.join([
                " WHERE proband_variant_id = {proband_variant_id}",
                " AND flag_name = '{flag_name}'"
            ]).format(
                proband_variant_id=self.escaped_model_attributes["proband_variant"].id,
                flag_name=self.escaped_model_attributes["flag_name"]
            )
        elif self.model_type == ProbandTranscriptVariant:
            if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
                table = 'SELECT * FROM ProbandTranscriptVariant'
            else:
                table = 'SELECT * FROM "ProbandTranscriptVariant"'
            cmd = ''.join([
                " WHERE transcript_id = {transcript_id}",
                " AND proband_variant_id = {proband_variant_id}"
            ]).format(
                transcript_id=self.escaped_model_attributes["transcript"].id,
                proband_variant_id=self.escaped_model_attributes["proband_variant"].id
            )
        elif self.model_type == ReportEvent:
            if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
                table = 'SELECT * FROM ReportEvent'
            else:
                table = 'SELECT * FROM "ReportEvent"'
            cmd = ''.join([
                " WHERE re_id = '{re_id}'",
                " AND proband_variant_id = {proband_variant_id}"
            ]).format(
                re_id=self.escaped_model_attributes["re_id"],
                proband_variant_id=self.escaped_model_attributes["proband_variant"].id
            )
        elif self.model_type == ToolOrAssemblyVersion:
            if settings.DATABASES['default']['ENGINE'] == 'django.db.backends.mysql':
                table = 'SELECT * FROM ToolOrAssemblyVersion'
            else:
                table = 'SELECT * FROM "ToolOrAssemblyVersion"'
            cmd = ''.join([
                " WHERE tool_name = '{tool_name}'",
                " AND version_number = '{version_number}'"
            ]).format(
                tool_name=self.escaped_model_attributes["tool_name"],
                version_number=self.escaped_model_attributes["version_number"]
            )

        sql =  ''.join([
            table,
            cmd
        ])
        return sql

    def check_found_in_db(self, queryset):
        """
        Queries the database for a model of the given type with the given
        attributes. Returns True if found, False if not.
        """
        sql_cmd = self.set_sql_cmd()

        entry = [
            db_obj for db_obj in self.model_type.objects.raw(sql_cmd)
        ]
        # tqdm.write(sql_cmd + "\t>>>\t" + str(entry))

        if len(entry) == 1:
            entry = entry[0]
            # also need to set self.entry here as it may not be called in init
            self.entry = entry
        elif len(entry) == 0:
            entry = False
            self.entry = entry
        else:
            print(entry)
            raise ValueError("Multiple entries found for same object.")

        return entry


class ManyCaseModel(object):
    """
    Class to deal with situations where we need to extend on CaseModel to allow
    for ManyToMany field population, as the bulk update must be handled using
    'through' tables.
    """
    def __init__(self, model_type, model_attributes_list, model_objects):
        self.model_type = model_type
        self.model_attributes_list = model_attributes_list
        self.model_objects = model_objects

        self.case_models = [
            CaseModel(model_type, model_attributes, model_objects)
            for model_attributes in model_attributes_list
        ]
        self.entries = self.get_entry_list()

    def get_entry_list(self):
        entries = []
        for case_model in self.case_models:
            entries.append(case_model.entry)
        return entries
