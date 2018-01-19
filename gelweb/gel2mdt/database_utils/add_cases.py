from ..api_utils import poll_api


class InterpretationList(object):
    """
    Represents the interpretation list from GeL CIP-API. Can be used to return
    a list of case numbers by status along with the hash of the current case data.
    """
    def __init__(self):
        self.all_cases = None
        self.all_cases_count = 0
        self.cases_to_poll = None  # 'sent_to_gmcs', 'report_generated', 'report_sent'

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
                "last_status": result["last_status"]}
                for result in request_list_results \
                if result["sample_type"] == "raredisease" \
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
            "report_sent"]
