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
                    and result['proband'] == self.sample
                       and result["last_status"] != "blocked"]
            else:
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
