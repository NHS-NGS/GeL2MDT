import os
import getpass
import requests
import json

import labkey as lk


class PollAPI(object):
    """
    Representation of an instance when an API has been polled. Contains info
    about the reponse including repsonse code, the json that has been returned,
    the API that has been polled.
    """
    def __init__(self, api, endpoint):
        self.api = api
        self.endpoint = endpoint

        self.server_list = {
            "cip_api": (
                "https://cipapi.genomicsengland.nhs.uk/api/2/{endpoint}",
                True),
            "panelapp": (
                "https://panelapp.genomicsengland.co.uk/WebServices/{endpoint}",
                False),
            "ensembl": (
                "http://rest.ensembl.org/{endpoint}",
                False),
            "mutalyzer": (
                "https://mutalyzer.nl/json/{endpoint}",
                False),
            "genenames": (
                "http://rest.genenames.org/{endpoint}",
                True)
        }

        self.server = self.server_list[api][0]
        self.url = self.server.format(endpoint=self.endpoint)
        self.headers_required = self.server_list[api][1]
        self.headers = None  # headers will be set if required, denoted in server_list tuple

        self.token_url = None  # only need this if auth headers required
        self.response_json = None  # set upon calling get_json_response()
        self.response_status = None

    def get_json_response(self):
        """
        Creates a session which polls the instance's API a maximum of 20 times
        for a json response, retrying if the poll fails.
        """
        json_poll_success = False
        while not json_poll_success:
            # set up request session to retry failed connections
            MAX_RETRIES = 20
            session = requests.Session()
            adapter = requests.adapters.HTTPAdapter(max_retries=MAX_RETRIES)
            session.mount("https://", adapter)
            if (self.headers_required) and (self.headers is None) and (self.api == 'cip_api'):
                # get auth headers if we need them and they're not yet set
                self.get_auth_headers()
                continue
            elif (self.headers_required) and (self.headers is None) and (self.api == 'genenames'):
                self.get_headers()
                continue
            elif (self.headers_required) and (self.headers is not None):
                # auth headers required; have been set
                response = session.get(
                    url=self.url,
                    headers=self.headers)
            elif not self.headers_required:
                # no headers required
                response = session.get(
                    url=self.url)

            try:
                # ensure that the json can be decoded to avoid MCA crash
                self.response_json = response.json()
                self.response_status = response.status_code
                json_poll_success = True
            except json.JSONDecodeError as e:
                continue

        return response.json()

    def get_credentials(self):
        """
        Asks user for username and password and sets these as environment variables to be accessed later.
        """
        try:
            user = os.environ["cip_api_username"]
        except KeyError as e:
            os.environ["cip_api_username"] = input("Enter username: ")
            os.environ["cip_api_password"] = getpass.getpass("Enter password: ")

    def get_auth_headers(self):
        """
        Creates a token then uses this to get authentication headers for CIP-API"
        """
        token_endpoint_list = {
            "cip_api": "get-token/"}
        token_endpoint = token_endpoint_list[self.api]

        self.token_url = self.server.format(endpoint=token_endpoint)
        self.get_credentials()
        token_response = requests.post(
            url=self.token_url,
            json=dict(
                username=os.environ["cip_api_username"],
                password=os.environ["cip_api_password"]
            ),
        )

        token_json = token_response.json()

        self.headers = {
            "Accept": "application/json",
            "Authorization": "JWT {token}".format(
                token=token_json.get("token"))}

    def get_headers(self):
        self.headers = {
            'Accept': 'application/json',
        }
