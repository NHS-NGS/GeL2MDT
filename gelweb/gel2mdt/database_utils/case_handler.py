import os
import json
import hashlib
from datetime import datetime

from ..models import *
from ..api_utils.poll_api import PollAPI
from ..vep_utils.run_vep_batch import CaseVariant, CaseTranscript


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
        self.json_variants \
            = self.json_case_data["json_request"]["TieredVariants"]

        self.panels = self.get_panels_json()
        self.variants = self.get_case_variants()
        self.transcripts = []  # set by MCM with a call to vep_utils

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

    def get_case_variants(self):
        """
        Create CaseVariant objects for each variant listed in the json,
        then return a list of all CaseVariants for construction of
        CaseTranscripts using VEP.
        """
        json_variants = self.json_variants
        case_variant_list = []
        # go through each variant in the json
        variant_object_count = 0
        for variant in json_variants:
            # check if it has any Tier1 or Tier2 Report Events
            variant_min_tier = None
            for report_event in variant["reportEvents"]:
                tier = int(report_event["tier"][-1])
                if variant_min_tier is None:
                    variant_min_tier = tier
                elif tier < variant_min_tier:
                    variant_min_tier = tier
            variant["max_tier"] = variant_min_tier

            if variant["max_tier"] < 3:
                variant_object_count += 1
                case_variant = CaseVariant(
                    chromosome=variant["chromosome"],
                    position=variant["position"],
                    ref=variant["reference"],
                    alt=variant["alternate"],
                    case_id=self.request_id,
                    variant_count=str(variant_object_count)
                )
                case_variant_list.append(case_variant)
                # also add it to the dict within self.json_variants
                variant["case_variant"] = case_variant
            else:
                # if the variant is Tier 3, assign False to the dict within
                # self.json_variants so we don't add a variant later
                variant["case_variant"] = False

        return case_variant_list


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
        elif self.model_type == Variant:
            case_model = self.get_variants()
        elif self.model_type == TranscriptVariant:
            case_model = self.get_transcript_variants()
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
                gene["EnsembleGeneIds"] = [None, ]

        genes = ManyCaseModel(Gene, [{
            "ensembl_id": gene["EnsembleGeneIds"][0],  # TODO: which ID to use?
            "hgnc_name": gene["GeneSymbol"]
        } for gene in gene_list])
        return genes

    def get_transcripts(self):
        """
        Create a ManyCaseModel for transcripts based on information returned
        from VEP.
        """
        # get list of gene case models
        genes = self.case.attribute_managers[Gene].case_model.case_models
        case_transcripts = self.case.transcripts
        # for each transcript, add an FK to the gene with matching ensg ID
        for transcript in case_transcripts:
            if not transcript.gene_ensembl_id:
                # if the transcript has no recognised gene associated
                continue  # don't bother checking genes
            for gene in genes:
                if gene.entry.ensembl_id == transcript.gene_ensembl_id:
                    transcript.gene_model = gene.entry

        transcripts = ManyCaseModel(Transcript, [{
            "gene": transcript.gene_model,
            "name": transcript.transcript_name,
            "canonical_transcript": transcript.transcript_canonical,
            "strand": transcript.transcript_strand
        # add all transcripts except those without associated genes
        } for transcript in case_transcripts if transcript.gene_ensembl_id])
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

    def get_variants(self):
        """
        Get the variant information (genetic position) for the variants in this
        case and return a matching ManyCaseModel with model_type = Variant.
        """
        # set and return the MCM
        variants = ManyCaseModel(Variant, [{
            "genome_assembly": self.case.json["assembly"],
            "alternate": variant["case_variant"].alt,
            "chromosome": variant["case_variant"].chromosome,
            "db_snp_id": variant["dbSNPid"],
            "reference": variant["case_variant"].ref,
            "position": variant["case_variant"].position,
        # loop through all variants and check that they have a case_variant
        # (all variants Tier1 and Tier2 do, Tier3 variants do not
        } for variant in self.case.json_variants if variant["case_variant"]])
        return variants

    def get_transcript_variants(self):
        """
        Get all variant transcripts. This is essentialy a 'through' table for
        the M2M relationship between Variant and Transcript, but with extra
        information.
        """
        # get all Transcript and Variant entries
        case_attribute_managers = self.case.attribute_managers
        transcript_manager = case_attribute_managers[Transcript]
        transcript_entries = [transcript.entry
                       for transcript in transcript_manager.case_models]
        variant_manager = case_attribute_managers[Variant]
        variant_entries = [variant.entry
                           for variant in variant_manager.case_models]

        # TODO: need some sort of way to link up Transcripts to the Variant
        # which they originate from in VEP
        # for each CaseTranscript (which contains necessary info):
        for case_transcript in self.case.case_transcripts:
            # add the corresponding Transcript entry
            for variant_entry in variant_entries:
                pass
            # add the corresponding Variant entry
            for transcript_entry in transcript_entries:
                pass

        # use the updated CaseTranscript instances to create an MCM
        transcript_variants = ManyCaseModel(TranscriptVariant, [{
            "transcript": None,
            "variant": None,
            "af_max": transcript.transcript_variant_af_max,
            "hgvs_c": transcript.transcript_variant_hgvs_c,
            "hgvs_p": transcript.transcript_variant_hgvs_p,
            "sift": transcript.variant_sift,
            "polyphen": transcript.variant_polyphen,
        } for transcript in case_transcripts])


    def get_proband_variants(self):
        """
        Get proband variant information from VEP and the JSON and create MCM.
        """
        ir_manager = self.case.attribute_managers[GELInterpretationReport]

        # match up created variants to corresponding dict in json_variants:
        variant_entries = [
            variant.entry
            for variant
            in self.case.attribute_managers[Variant].case_model.case_models
        ]
        for json_variant in self.case.json_variants:
            # some json_variants won't have an entry (T3), so:
            json_variant["variant_entry"] = None
            # for those that do, fetch from list of entries:
            for variant in variant_entries:
                if (
                    json_variant["position"] == variant.position and
                    json_variant["reference"] == variant.reference and
                    json_variant["alternate"] == variant.alternate
                ):
                    print("Found matching json_variant matching entry")
                    json_variant["variant_entry"] = variant

        proband_variants = ManyCaseModel(ProbandVariant, [{
            "interpretation_report": ir_manager.case_model.entry,
            "max_tier": variant["max_tier"],
            "variant": variant["variant_entry"]
        # only adding T1/2
        } for variant in self.case.json_variants if variant["variant_entry"]])
        return proband_variants

    def get_proband_transcript_variants(self):
        pass

    def get_report_events(self):
       """
       Get all the report events for each case from the json and populate an
       MCM with this information.
       """
       # get gene and panel entries
       genes = [gene.entry for gene
                in self.case.attribute_managers[Gene].case_model.case_models]
       panels = [panel.entry for panel
                 in self.case.attribute_managers[Panel].case_model.case_models]
       # get list of dicts of each report event
       json_report_events = []
       for variant in self.case.json_variants:
           for report_event in variant["reportEvents"]:
                json_report_events.append({
                    # TODO: fetch coverage info from elsewhere in json
                    "coverage": None,
                    # TODO: add information about RE from json
                    "gene": None,
                    "mode_of_inheritance": report_event["modeOfInheritance"],
                    "panel": None,
                    "penetrance": report_event["penetrance"],
                    "phenotype": None,
                    "proband_variant": None,
                    "re_id": report_event["reportEventId"],
                    "tier": int(report_event["tier"][-1:])
                })

       report_events = ManyCaseModel(ReportEvent, json_report_events)
       return report_events

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
