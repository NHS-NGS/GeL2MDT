import os
import json
import hashlib

from ..models import *
from ..api_utils import poll_api


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

        self.case_attributes = {
            # CaseModels for each of the required Models, to be set by MCA
            "clinician": None,
            "family": None,
            "phenotypes": None,
            "ir_family": None,
            "panels": None,
            "panel_versions": None,
            "genes": None,
            "transcripts": None,
            "ir": None,
            "proband_variants": None,
            "proband_transcript_variants": None,
            "report_events": None,
            "tools_and_assemblies": None,
            "tool_and_assembly_versions": None

        }

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
        status_keys = status_json.keys()
        max_key = max(status_keys)
        return status_jsons[max_key]  # assuming GeL will always work upwards..

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
        self.clinician = clinician

    def get_family(self):
        """
        Create case model to handle adding/getting family for this case.
        """
        family = CaseModel(Family, {
            "clinician": self.clinician.entry,
            "gel_family_id": int(self.json["family_id"])
        })
        self.family = family

    def get_phenotypes(self):
        """
        Create a list of CaseModels for phenotypes for this case.
        """
        phenotypes = ManyCaseModel(Phenotype, [
            {"hpo_terms": phenotype["term"],
             "description": "unknown"}
            for phenotype in self.proband["hpoTermList"]
            if phenotype["termPresence"] is True
        ])
        self.phenotypes = phenotypes

    def get_ir_family(self):
        """
        Create a CaseModel for the new IRFamily Model to be added to the
        database (unlike before it is impossible that this alreay exists).
        """
        ir_family = CaseModel(InterpretationReportFamily, {
            "participant_family": self.family,
            "cip": self.json["cip"],
            "ir_family_id": self.request_id,
            "priority": self.json["case_priority"]
        })
        return ir_family

    def update_case(self):
        """
        Update a case that has a recorded IRfamily but with a mismatching
        hash value on the latest IR record.
        """
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
