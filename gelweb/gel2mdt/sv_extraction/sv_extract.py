from ..api_utils.poll_api import PollAPI
import tempfile
import requests
from bs4 import BeautifulSoup
from urllib import urlopen

class SVExtraction:
    def __init__(self, ir, ir_version):
        self.ir = ir
        self.ir_version = ir_version
        self.html_version = None
        self.filepath = None
        self.tempfile = tempfile.NamedTemporaryFile(mode='w+b', delete=False)
        self.sv_data = []

    def download_cip_json(self):
        request_poll = PollAPI(
            # instantiate a poll of CIP API for a given case json
            "cip_api", "interpretation-request/{id}/{version}?reports_v6=true".format(
                id=self.ir,
                version=self.ir_version))
        response = request_poll.get_json_response()
        for file in response['files']:
            if 'supplementary' in file['file_name']:
                url_name = file['url'].split('/')[-3]
                self.filepath = url_name

    def download_html(self):
        request_poll = PollAPI(
            # instantiate a poll of CIP API for a given case json
            "cip_api", f"file/{self.filepath}/download-file/")
        request_poll.get_auth_headers()
        session = requests.Session()
        adapter = requests.adapters.HTTPAdapter(max_retries=20)
        session.mount("https://", adapter)
        response = session.get(url=request_poll.url,
                               headers=request_poll.headers,
                               stream=True)
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:  # filter out keep-alive new chunks
                self.tempfile.write(chunk)
        self.tempfile.close()

    def parse_html(self):
        with open(self.tempfile.name) as f:
            webpage = f.read()
        soup = BeautifulSoup(webpage)
        table = soup.find("div", id="svcnv")
        for row in table.find_all("tr"):
            columns = []
            cols = row.find_all("td")
            for ele in cols:
                br = ele.find_all('br')
                if br:
                    ele_list = [string for string in ele.strings]
                    columns.append(ele_list)
                else:
                    columns.append(ele.text.strip())
            self.sv_data.append(columns)

    def
