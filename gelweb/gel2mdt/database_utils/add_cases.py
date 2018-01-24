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
        self.request_id = str(
            self.json["interpretation_request_id"]) \
            + "-" + str(self.json["version"])

        self.json_hash = self.hash_json()

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

    def add_case(self):
        """
        Add a new case that has no recorded IRfamily to the database.
        """
        # TODO: add LabKey support!!
        self.clinician = CaseModel(Clinician, {
            "name": "unknown",
            "email": "unknown",
            "hospital": "unknown"
        })

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
        self.created = self.check_found_in_db()

    def check_found_in_db(self):
        """
        Queries the database for a model of the given type with the given
        attributes. Returns True if found, False if not.
        """
        try:
            created = self.model_type.objects.get(
            **self.model_attributes
        )  # returns True if corresponding instance exists
        except self.model_type.DoesNotExist as e:
            created = False
        return created


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
        self.cases_to_skip = set(self.list_of_cases) - set(self.cases_to_add) - \
            set(self.cases_to_update)

        # begin update process
        # --------------------
        self.update_errors = {}

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
        request_poll = poll_api.PollAPI(
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


class InterpretationList(object):
    """
    Represents the interpretation list from GeL CIP-API. Can be used to return
    a list of case numbers by status along with the hash of the current case
    data.
    """
    def __init__(self):
        self.all_cases = self.get_all_cases()
        self.cases_to_poll = self.get_poll_cases()

    def get_all_cases(self):
        """
        Invokes PollAPI to retrieve a list of all the cases available to a
        given user, then returns a list of cases which are raredsease and not
        blocked.
        """
        all_cases = []
        last_page = False
        page = 1
        while not last_page:
            request_list_poll = poll_api.PollAPI(
                "cip_api",
                "interpretation-request?page={page}".format(page=page)
            )
            request_list_poll.get_json_response()
            request_list_results = request_list_poll.response_json["results"]

            all_cases += [{
                # add the ir_id, sample type, and latest status to dict
                "interpretation_request_id":
                    result["interpretation_request_id"],
                "sample_type":
                    result["sample_type"],
                "last_status":
                    result["last_status"]}
                for result in request_list_results
                if result["sample_type"] == "raredisease"
                and result["last_status"] != "blocked"]

            if request_list_poll.response_json["next"]:
                page += 1
            else:
                last_page = True

        self.all_cases_count = request_list_poll.response_json["count"]
        return all_cases

    def get_poll_cases(self):
        """
        Removes cases from self.all_cases which are not of interest, ie. keep
        only 'sent_to_gmcs', 'report_generated', 'report_sent'.
        """
        cases_to_poll = [
            case for case in self.all_cases if case["last_status"] in [
                "sent_to_gmcs",
                "report_generated",
                "report_sent"]]

        return cases_to_poll
