from django.test import TestCase
from .api_utils import poll_api
from .database_utils import add_cases

class Poll_CIP_API_TestCase(TestCase):
    def test_returns_status_code(self):
        cip_api_poll = poll_api.PollAPI("cip_api", "interpretation-request")
        cip_api_poll.get_json_response()


class TestInterpretationList(TestCase):
    def test_get_list_of_jsons(self):
        get_list = add_cases.InterpretationList()
        get_list.get_interpretation_list()
        case_list = get_list.all_cases

        assert isinstance(case_list, list)
        for case in case_list:
            assert isinstance(case, dict)

    def test_only_get_raredisease(self):
        pass

    def test_get_cases_of_interest(self):
        get_list = add_cases.InterpretationList()
        get_list.get_interpretation_list()
        cases_to_poll = get_list.cases_to_poll

        for case in cases_to_poll:
            assert case["last_status"] in ["sent_to_gmcs","report_generated","report_sent"]
