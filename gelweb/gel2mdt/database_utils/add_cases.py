import os
import json
import hashlib

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
            self.json["interpretation_request_id"]) + "-" + str(self.json["version"])

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
        self.json_hash = hash_digest


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
        # are we using test data files? defaults False (no)
        self.test_data = test_data
        if self.test_data:
            # set list_of_cases to test zoo
            self.list_of_case = self.fetch_test_data()
            self.cases_to_poll = None
        else:
            # set list_of_cases to cases of interest from API
            interpretation_list_poll = InterpretationList()
            self.cases_to_poll = interpretation_list_poll.cases_to_poll
            self.list_of_case = self.fetch_api_data()

        self.cases_to_add = None          # new cases (no IRfamily)
        self.cases_to_update = None       # cases w/ different hash (IRfamily exists)
        self.update_errors = {}           # holds errors that are raised during updates

    def fetch_test_data(self):
        """
        This will run and convert our test data to a list of jsons if
        self.test_data is set to True.
        """
        list_of_cases = []
        for filename in os.listdir(os.path.join(os.getcwd(), "gel2mdt/tests/test_files")):
            file_path = os.path.join(
                os.getcwd(), "gel2mdt/tests/test_files/{filename}".format(
                    filename=filename))
            with open(file_path) as json_file:
                json_data = json.load(json_file)
                list_of_cases.append(Case(case_json=json_data))

        return list_of_cases

    def fetch_api_data(self):
        list_of_cases = [
            Case(
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
        pass

    def check_cases_to_update(self):
        """
        Go through list of cases that _do not_ need to be added and check
        hashes against the latest case stored for corresponding IRfamily
        entries.
        """
        pass


class InterpretationList(object):
    """
    Represents the interpretation list from GeL CIP-API. Can be used to return
    a list of case numbers by status along with the hash of the current case data.
    """
    def __init__(self):
        self.all_cases = None
        self.all_cases_count = 0
        self.cases_to_poll = None  # 'sent_to_gmcs', 'report_generated', 'report_sent'

        self.get_interpretation_list()

    def get_interpretation_list(self):
        """
        Invokes PollAPI to retrieve a list of all the cases available to a
        given user, then sets them to the corresponding class attributes.
        """
        last_page = False
        page = 1

        all_cases = []

        while not last_page:
            request_list_poll = poll_api.PollAPI(
                "cip_api", "interpretation-request?page={page}".format(page=page)
            )
            request_list_poll.get_json_response()
            request_list_results = request_list_poll.response_json["results"]

            all_cases += [{
                "interpretation_request_id": result["interpretation_request_id"],
                "sample_type": result["sample_type"],
                "last_status": result["last_status"]}
                for result in request_list_results
                if result["sample_type"] == "raredisease"
                and result["last_status"] != "blocked"]

            if request_list_poll.response_json["next"]:
                page += 1
            else:
                last_page = True

        self.all_cases_count = request_list_poll.response_json["count"]
        self.all_cases = all_cases
        self.cases_to_poll = [case for case in all_cases if case["last_status"] in [
            "sent_to_gmcs",
            "report_generated",
            "report_sent"]]
