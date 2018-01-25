import os
import json
import hashlib
from datetime import datetime

from ..models import *
from ..api_utils.poll_api import PollAPI


class Case(object):
    """
    Representation of a single case which can be added to the database,
    updated in the database, or skipped dependent on whether a matching
    case/case family is found.
    """
    def __init__(self, case_json):
        self.json = case_json
        self.json_case_data = self.json["interpretation_request_data"]
        self.request_id = str(
            self.json["interpretation_request_id"]) \
            + "-" + str(self.json["version"])

        self.json_hash = self.hash_json()
        self.proband = self.get_proband_json()
        self.status = self.get_status_json()

        self.panels = self.get_panels_json()

        # initialise a dict to contain the AttributeManagers for this case,
        # which will be set by the MCA as they are required (otherwise there
        # are missing dependencies)
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
        participant_jsons = \
            self.json_case_data["json_request"]["pedigree"]["participants"]
        proband_json = None
        for participant in participant_jsons:
            if participant["isProband"]:
                proband_json = participant
        return proband_json

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
        json_request = self.json_case_data["json_request"]
        return json_request["pedigree"]["analysisPanels"]


class CaseAttributeManager(object):
    """
    Handler for managing each different type of case attribute.
    Holds get/refresh functions to be called by MCA, as well as pointing to
    CaseModels and ManyCaseModels for access by MCA.bulk_create_new().
    """
    def __init__(self, case, model_type, many=False):
        """
        Initialise with CaseModel or ManyCaseModel, dependent on many param.
        """
        self.case = case  # for accessing related table entries
        self.model_type = model_type
        self.many = many
        self.case_model = self.get_case_model()

    def get_case_model(self):
        """
        Call the corresponding function to update the case model within the
        AttributeManager.
        """
        if self.model_type == Clinician:
            case_model = self.get_clinician()
        elif self.model_type == Family:
            case_model = self.get_family()
        elif self.model_type == Phenotype:
            case_model = self.get_phenotypes()
        elif self.model_type == InterpretationReportFamily:
            case_model = self.get_ir_family()
        elif self.model_type == Panel:
            case_model = self.get_panels()
        elif self.model_type == PanelVersion:
            case_model = self.get_panel_versions()
        elif self.model_type == Gene:
            case_model = self.get_genes()
        elif self.model_type == Transcript:
            case_model = self.get_transcripts()
        elif self.model_type == GELInterpretationReport:
            case_model = self.get_ir()
        elif self.model_type == ProbandVariant:
            case_model = self.get_proband_variants()
        elif self.model_type == ProbandTranscriptVariant:
            case_model = self.get_proband_transcript_variants()
        elif self.model_type == ReportEvent:
            case_model = self.get_report_events()
        elif self.model_type == ToolOrAssembly:
            case_model = self.get_tools_and_assemblies()
        elif self.model_type == ToolOrAssemblyVersion:
            case_model = self.get_tool_and_assembly_versions()

        return case_model

    def get_clinician(self):
        """
        Create a case model to handle adding/getting the clinician for case.
        """
        # TODO: add LabKey support!!
        clinician = CaseModel(Clinician, {
            "name": "unknown",
            "email": "unknown",
            "hospital": "unknown"
        })
        return clinician

    def get_family(self):
        """
        Create case model to handle adding/getting family for this case.
        """
        clinician = self.case.attribute_managers[Clinician].case_model
        family = CaseModel(Family, {
            "clinician": clinician.entry,
            "gel_family_id": int(self.case.json["family_id"])
        })
        return family

    def get_phenotypes(self):
        """
        Create a list of CaseModels for phenotypes for this case.
        """
        phenotypes = ManyCaseModel(Phenotype, [
            {"hpo_terms": phenotype["term"],
             "description": "unknown"}
            for phenotype in self.case.proband["hpoTermList"]
            if phenotype["termPresence"] is True
        ])
        return phenotypes

    def get_panels(self):
        """
        Poll panelApp to fetch information about a panel, then create a
        ManyCaseModel with this information.
        """
        for panel in self.case.panels:
            panelapp_poll = PollAPI(
                "panelapp", "get_panel/{panelapp_id}".format(
                    panelapp_id=panel["panelName"])
            )
            panelapp_poll.get_json_response()
            panel["panelapp_results"] = panelapp_poll.response_json["result"]

        panels = ManyCaseModel(Panel, [{
            "panelapp_id": panel["panelName"],
            "panel_name": panel["panelapp_results"]["SpecificDiseaseName"],
            "disease_group": panel["panelapp_results"]["DiseaseGroup"],
            "disease_subgroup": panel["panelapp_results"]["DiseaseSubGroup"]
        } for panel in self.case.panels])
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

        for panel in self.case.panels:
            # set self.case.panels["model"] to the correct model
            for panel_model in panel_models:
                if panel["panelName"] == panel_model.panelapp_id:
                    panel["model"] = panel_model

        panel_versions = ManyCaseModel(PanelVersion, [{
            # create the MCM
            "version_number": panel["panelapp_results"]["version"],
            "panel": panel["model"]
        } for panel in self.case.panels])
        return panel_versions

    def get_genes(self):
        """
        Create gene objects from the genes from panelapp.
        """
        panels = self.case.panels
        # get the list of genes from the panelapp_result
        gene_list = []
        for panel in panels:
            genes = panel["panelapp_results"]["Genes"]
            gene_list += genes

        for gene in gene_list:
            if len(gene["EnsembleGeneIds"]) == 0:
                gene["EnsembleGeneIds"] = [None,]

        genes = ManyCaseModel(Gene, [{
            "ensembl_id": gene["EnsembleGeneIds"][0],  # TODO: which ID to use?!
            "hgnc_name": gene["GeneSymbol"]
        } for gene in gene_list])
        return genes

    def get_transcripts(self):
        pass

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
        })
        return ir_family

    def get_ir(self):
        """
        Get json information about an Interpretation Report and create a
        CaseModel from it.
        """
        case_attribute_managers = self.case.attribute_managers
        irf_manager = case_attribute_managers[InterpretationReportFamily]
        ir_family = irf_manager.case_model

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
            "user": self.case.status["user"]
        })
        return ir

    def get_proband_variants(self):
        pass

    def get_proband_transcript_variants(self):
        pass

    def get_report_events(self):
        pass

    def get_tools_and_assemblies(self):
        pass

    def get_tool_and_assembly_versions(self):
        pass


class CaseModel(object):
    """
    A handler for an instance of a model that belongs to a case. Holds an
    instance of a model (pre-creation or post-creation) and whether it
    requires creation in the database.
    """
    def __init__(self, model_type, model_attributes):
        self.model_type = model_type
        self.model_attributes = model_attributes
        self.entry = self.check_found_in_db()

    def check_found_in_db(self):
        """
        Queries the database for a model of the given type with the given
        attributes. Returns True if found, False if not.
        """
        try:
            entry = self.model_type.objects.get(
                **self.model_attributes
            )  # returns True if corresponding instance exists
        except self.model_type.DoesNotExist as e:
            entry = False
        return entry


class ManyCaseModel(object):
    """
    Class to deal with situations where we need to extend on CaseModel to allow
    for ManyToMany field population, as the bulk update must be handled using
    'through' tables.
    """
    def __init__(self, model_type, model_attributes_list):
        self.model_type = model_type
        self.model_attributes_list = model_attributes_list

        self.case_models = [
            CaseModel(model_type, model_attributes)
            for model_attributes in model_attributes_list
        ]
        self.entries = self.get_entry_list()

    def get_entry_list(self):
        entries = []
        for case_model in self.case_models:
            entries.append(case_model.entry)
        return entries
