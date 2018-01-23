import unittest
from django.test import TestCase
from .api_utils import poll_api
from .database_utils import add_cases

import re
import os
import json
import hashlib


@unittest.skip("skipping to avoid polling")
class Poll_CIP_API_TestCase(TestCase):
    def test_returns_status_code(self):
        cip_api_poll = poll_api.PollAPI("cip_api", "interpretation-request")
        cip_api_poll.get_json_response()


@unittest.skip("skip to avoid polling")
class TestInterpretationList(TestCase):
    def setUp(self):
        self.case_list_handler = add_cases.InterpretationList()
        self.case_list = self.case_list_handler.all_cases
        self.cases_to_poll = self.case_list_handler.cases_to_poll

    def test_get_list_of_jsons(self):
        assert isinstance(self.case_list, list)
        for case in self.case_list:
            assert isinstance(case, dict)

    def test_only_get_raredisease(self):
        for case in self.case_list:
            assert case["sample_type"] == "raredisease"

    def test_get_cases_of_interest(self):
        for case in self.cases_to_poll:
            assert case["last_status"] in [
                "sent_to_gmcs",
                "report_generated",
                "report_sent"]


class TestAddCases(TestCase):
    def setUp(self):
        """
        Instantiate a MultipleCaseAdder for the zoo of test cases.
        """
        self.case_update_handler = add_cases.MultipleCaseAdder(test_data=True)

    def test_request_id_format(self):
        """
        For each test case, assert that we correctly parse the IR ID.
        """
        for case in self.case_update_handler.list_of_cases:
            assert re.match("\d+-\d+", case.request_id)

    def test_hash_cases(self):
        """
        For each test case, assert that we reliably hash the json.
        """
        test_json_hashes = {}
        for filename in os.listdir(
            os.path.join(
                os.getcwd(),
                "gel2mdt/tests/test_files"
            )
        ):
            # get the jsons
            file_path = os.path.join(
                os.getcwd(), "gel2mdt/tests/test_files/{filename}".format(
                    filename=filename))
            with open(file_path) as json_file:
                json_data = json.load(json_file)
            # get the IR ID and hash the json into a dict
            request_id = str(json_data["interpretation_request_id"]) + \
                "-" + str(json_data["version"])
            test_json_hashes[request_id] = hashlib.sha512(
                json.dumps(json_data, sort_keys=True).encode('utf-8')
            ).hexdigest()

        for case in self.case_update_handler.list_of_cases:
            assert case.json_hash == test_json_hashes[case.request_id]
