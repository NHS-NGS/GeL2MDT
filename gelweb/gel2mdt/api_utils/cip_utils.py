"""Copyright (c) 2018 Great Ormond Street Hospital for Children NHS Foundation
Trust & Birmingham Women's and Children's NHS Foundation Trust

Permission is hereby granted, free of charge, to any person obtaining a copy of
this software and associated documentation files (the "Software"), to deal in
the Software without restriction, including without limitation the rights to
use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies
of the Software, and to permit persons to whom the Software is furnished to do
so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""
from .poll_api import PollAPI


class InterpretationList(object):
    """
    Represents the interpretation list from GeL CIP-API. Can be used to return
    a list of case numbers by status along with the hash of the current case
    data.
    """
    def __init__(self, sample_type, sample=None):
        self.sample_type = sample_type
        self.sample = sample
        self.all_cases = self.get_all_cases()
        self.cases_to_poll = self.get_poll_cases()
        self.blocked_cases = self.get_blocked_cases()

    def get_all_cases(self):
        """
        Invokes PollAPI to retrieve a list of all the cases available to a
        given user.
        """
        all_cases = []
        west_london_codes = ['RYJ', 'RQM', 'RPY', 'RT3', 'RYJ99', 'TRX', 'CW', 'FPNE', 'WM', 'WLGMC']
        last_page = False
        page = 1
        while not last_page:
            request_list_poll = PollAPI(
                "cip_api",
                "interpretation-request?page={page}".format(page=page)
            )
            request_list_poll.get_json_response()
            request_list_results = request_list_poll.response_json["results"]

            if self.sample:
                all_cases += [{
                    # add the ir_id, sample type, and latest status to dict
                    "interpretation_request_id":
                        result["interpretation_request_id"],
                    "sample_type":
                        result["sample_type"],
                    "last_status":
                        result["last_status"]}
                    for result in request_list_results
                    if result["sample_type"] == self.sample_type
                    and result['proband'] == self.sample]
            else:
                for result in request_list_results:
                    download = True
                    if result["sample_type"] == self.sample_type and not result['proband'].startswith('12000'):
                        if not result['sites']:
                            pass  # Download just in case
                        elif len(result['sites']) > 1:
                            part_of_west_london = []
                            for site in result['sites']:
                                part_of_west_london.append(any([f.startswith(site) for f in west_london_codes]))
                            if all(part_of_west_london):
                                download = False
                        elif any([f.startswith(result['sites'][0]) for f in west_london_codes]):
                            download = False
                        if download:
                            all_cases.append({
                                # add the ir_id, sample type, and latest status to dict
                                "interpretation_request_id":
                                    result["interpretation_request_id"],
                                "sample_type":
                                    result["sample_type"],
                                "last_status":
                                    result["last_status"]})

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
        status_lookup = {'raredisease': [ "sent_to_gmcs", "report_generated", "report_sent"],
                         'cancer': ['interpretation_generated', "sent_to_gmcs", "report_generated", "report_sent"]}
        cases_to_poll = [
            case for case in self.all_cases if case["last_status"] in status_lookup[self.sample_type]]

        return cases_to_poll

    def get_blocked_cases(self):
        """
        Finds all cases with a blocked status so the status of these cases can be updated
        """
        blocked_cases = [case for case in self.all_cases if case["last_status"] == 'blocked']
        return blocked_cases
