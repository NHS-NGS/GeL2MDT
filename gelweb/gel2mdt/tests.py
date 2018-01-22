import unittest
from django.test import TestCase
from .api_utils import poll_api
from .database_utils import add_cases

import re

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
        self.case_update_handler = add_cases.MultipleCaseAdder(test_data=True)

    def test_request_id_format(self):
        print(self.case_update_handler.list_of_cases)
        for case in self.case_update_handler.list_of_cases:
            print(case.request_id)
            assert re.match("\d+-\d+", case.request_id)
