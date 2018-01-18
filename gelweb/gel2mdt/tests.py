from django.test import TestCase
from .api_utils import poll_api

class PollAPITestCase(TestCase):
    def test_cip_api_poll(self):
        cip_api_poll = poll_api.PollAPI("cip_api", "interpretation-request")
    print(cip_api_poll.response_status)
