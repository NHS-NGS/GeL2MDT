import os
import json

from ..models import *
from ..api_utils.poll_api import PollAPI
from ..api_utils.cip_utils import InterpretationList
from .case_handler import Case


class MultipleCaseAdder(object):
    """
    Representation of the process of adding many cases to the database.
    This class will handle the checking of cases already present, adding
    required related instances to the database and reporting status and
    errors during the process.
    """
    def __init__(self, test_data=False):
        """
        Initiliase an instance of a MultipleCaseAdder to start managing
        a database update. This will get the list of cases available to
        us, hash them all, check which need to be added/updated and then
        manage the updating of the database.
        :param test_data: Boolean. Use test data or not. Default = False
        """

        # fetch and identify cases to add or update
        # -----------------------------------------
        # are we using test data files? defaults False (no)
        self.test_data = test_data
        if self.test_data:
            # set list_of_cases to test zoo
            self.list_of_cases = self.fetch_test_data()
            self.cases_to_poll = None
        else:
            # set list_of_cases to cases of interest from API
            interpretation_list_poll = InterpretationList()
            self.cases_to_poll = interpretation_list_poll.cases_to_poll
            self.list_of_cases = self.fetch_api_data()

        self.cases_to_add = self.check_cases_to_add()
        self.cases_to_update = self.check_cases_to_update()
        self.cases_to_skip = set(self.list_of_cases) - \
            set(self.cases_to_add) - \
            set(self.cases_to_update)

        # begin update process
        # --------------------
        self.update_errors = {}
        self.add_cases()
        self.update_cases()

    def fetch_test_data(self):
        """
        This will run and convert our test data to a list of jsons if
        self.test_data is set to True.
        """
        list_of_cases = []
        for filename in os.listdir(
            # get list of test files then open and load to json
            os.path.join(
                os.getcwd(), "gel2mdt/tests/test_files")):
            file_path = os.path.join(
                os.getcwd(), "gel2mdt/tests/test_files/{filename}".format(
                    filename=filename))
            with open(file_path) as json_file:
                json_data = json.load(json_file)
                list_of_cases.append(Case(case_json=json_data))
        return list_of_cases

    def fetch_api_data(self):
        list_of_cases = [
            # list comprehension, calling self.get_case_json each time for poll
            Case(
                # instatiate a new case with the polled json
                case_json=self.get_case_json(case["interpretation_request_id"])
            ) for case in self.cases_to_poll
        ]
        return list_of_cases

    def get_case_json(self, interpretation_request_id):
        """
        Take an interpretation request ID, then get the json for that case
        using the PollAPI class defined in .database_utils
        :param interpretation_request_id: an IR ID of the format XXXX-X
        :returns: A case json associated with the given IR ID from CIP-API
        """
        request_poll = PollAPI(
            # instantiate a poll of CIP API for a given case json
            "cip_api", "interpretation-request/{id}/{version}".format(
                id=interpretation_request_id.split("-")[0],
                version=interpretation_request_id.split("-")[1]))
        request_poll.get_json_response()

    def check_cases_to_add(self):
        """
        Go through list of cases and check family ID against database
        entries for IRfamily. Return the list of cases for which no IRfamily
        exists.
        """
        database_cases = InterpretationReportFamily.objects.all().values_list(
            'ir_family_id', flat=True
        )

        cases_to_add = []
        for case in self.list_of_cases:
            if case.request_id not in database_cases:
                cases_to_add.append(case)
        return cases_to_add

    def check_cases_to_update(self):
        """
        Go through list of cases that _do not_ need to be added and check
        hashes against the latest case stored for corresponding IRfamily
        entries.
        """
        cases_to_update = []
        # use set subtraction to get only cases that haven't already been added
        cases_to_check = set(self.list_of_cases) - set(self.cases_to_add)
        try:
            latest_report_list = [
                GELInterpretationReport.objects.filter(
                    ir_family=InterpretationReportFamily.objects.get(
                        ir_family_id=case.request_id
                    )).latest("updated") for case in cases_to_check]

            latest_hashes = {
                ir.ir_family.ir_family_id: ir.sha_hash
                for ir in latest_report_list
            }

            for case in cases_to_check:
                if case.json_hash != latest_hashes[case.request_id]:
                    cases_to_update.append(case)

        except GELInterpretationReport.DoesNotExist as e:
            # no such cases.
            pass

        return cases_to_update

    def add_cases(self):
        """
        Adds the cases to the database which required adding.
        """
        # clinicians
        # ----------
        # set the values for each clinician
        for case in self.cases_to_add:
            case.get_clinician()
        # get the clinicians, find new ones, bulk update these
        clinicians = [case.clinician for case in self.cases_to_add]
        self.bulk_create_new(Clinician, clinicians)
        # ensure case.clinician is refreshed for ones with new-created clins
        for clinician in clinicians:
            if clinician.entry is False:
                clinician.entry = clinician.check_found_in_db()
                # above sets the CaseModel attribute, now refresh family attrs

        # family
        # ------
        # set the values for each family
        for case in self.cases_to_add:
            case.get_family()
        # bulk update new families
        families = [case.family for case in self.cases_to_add]
        self.bulk_create_new(Family, families)
        for family in families:
            if family.entry is False:
                family.entry = family.check_found_in_db()

        # phenotypes
        # ---------
        # set phenotype values for each family
        phenotypes = []
        for case in self.cases_to_add:
            case.get_phenotypes()
            # first bulk update the phenotypes for each case
            phenotypes += case.phenotypes.case_models
        self.bulk_create_new(Phenotype, phenotypes)
        # ensure ManyCaseModel instances are aware of newly created phenotypes
        for case in self.cases_to_add:
            for phenotype in case.phenotypes.case_models:
                if phenotype.entry is False:
                    phenotype.entry = phenotype.check_found_in_db
            case.phenotypes.entries = case.phenotypes.get_entry_list()

    def bulk_create_new(self, model_type, model_list):
        """
        Takes a list of CaseModel instances of a given model_type, then creates
        a list of unique attribute sets for that particular list of instances.
        This list of unique attributes can then be passed to a bulk_create
        function to update the database.
        """
        # get the attribute dicts for ModelCases which have no database entry
        new_attributes = [
            case_model.model_attributes
            for case_model in model_list
            if case_model.entry is False]
        # use sets and tuples to remove duplicate dictionaries
        new_attributes = [
            dict(attribute_tuple)
            for attribute_tuple
            in set([
                tuple(attribute_dict.items())
                for attribute_dict
                in new_attributes])]
        # bulk create database entries from the list of unique new attributes
        model_type.objects.bulk_create([
            model_type(**attributes)
            for attributes in new_attributes])

    def update_cases(self):
        """
        Updates the cases to the database which required updating.
        """
        pass
