import os
import json

from ..models import *
from ..api_utils.poll_api import PollAPI
from ..api_utils.cip_utils import InterpretationList
from ..vep_utils.run_vep_batch import generate_transcripts
from .case_handler import Case, CaseAttributeManager

import pprint
import logging


# set up logging
logger = logging.getLogger(__name__)


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
        logger.info("Initialising a MultipleCaseAdder.")

        # fetch and identify cases to add or update
        # -----------------------------------------
        # are we using test data files? defaults False (no)
        self.test_data = test_data
        if self.test_data:
            logger.info("Fetching test data.")
            # set list_of_cases to test zoo
            self.list_of_cases = self.fetch_test_data()
            self.cases_to_poll = None
            logger.info("Fetched test data.")
        else:
            # set list_of_cases to cases of interest from API
            logger.info("Fetching live API data.")
            logger.info("Polling for list of available cases...")
            interpretation_list_poll = InterpretationList()
            logger.info("Fetched available cases")

            logger.info("Determining which cases to poll...")
            self.cases_to_poll = interpretation_list_poll.cases_to_poll

            logger.info("Fetching API JSON data for cases to poll...")
            self.list_of_cases = self.fetch_api_data()

            logger.info("Fetched all required CIP API data.")


        logger.info("Checking which cases to add.")
        self.cases_to_add = self.check_cases_to_add()
        logger.info("Checking which cases require updating.")
        self.cases_to_update = self.check_cases_to_update()#
        self.cases_to_skip = set(self.list_of_cases) - \
            set(self.cases_to_add) - \
            set(self.cases_to_update)



        # begin update process
        # --------------------
        self.update_errors = {}
        logger.info("Adding cases from cases_to_add.")
        self.add_cases()
        logger.info("Adding cases from cases_to_update.")
        self.update_cases()

    def fetch_test_data(self):
        """
        This will run and convert our test data to a list of jsons if
        self.test_data is set to True.
        """
        list_of_cases = []
        for filename in os.listdir(
            # get list of test files then open and load to json
            os.path.join(
                os.getcwd(), "gel2mdt/tests/test_files")):
            file_path = os.path.join(
                os.getcwd(), "gel2mdt/tests/test_files/{filename}".format(
                    filename=filename))
            logger.info("Found case json at", file_path, "for testing.")
            with open(file_path) as json_file:
                json_data = json.load(json_file)
                list_of_cases.append(Case(case_json=json_data))
        logger.info("Found", len(list_of_cases), "test cases.")
        return list_of_cases

    def fetch_api_data(self):
        list_of_cases = [
            # list comprehension, calling self.get_case_json each time for poll
            Case(
                # instatiate a new case with the polled json
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
        request_poll = PollAPI(
            # instantiate a poll of CIP API for a given case json
            "cip_api", "interpretation-request/{id}/{version}".format(
                id=interpretation_request_id.split("-")[0],
                version=interpretation_request_id.split("-")[1]))
        return request_poll.get_json_response()

    def check_cases_to_add(self):
        """
        Go through list of cases and check family ID against database
        entries for IRfamily. Return the list of cases for which no IRfamily
        exists.
        """
        database_cases = InterpretationReportFamily.objects.all().values_list(
            'ir_family_id', flat=True
        )

        cases_to_add = []
        for case in self.list_of_cases:
            if case.request_id not in database_cases:
                cases_to_add.append(case)
        return cases_to_add

    def check_cases_to_update(self):
        """
        Go through list of cases that _do not_ need to be added and check
        hashes against the latest case stored for corresponding IRfamily
        entries.
        """
        cases_to_update = []
        # use set subtraction to get only cases that haven't already been added
        cases_to_check = set(self.list_of_cases) - set(self.cases_to_add)
        try:
            latest_report_list = [
                GELInterpretationReport.objects.filter(
                    ir_family=InterpretationReportFamily.objects.get(
                        ir_family_id=case.request_id
                    )).latest("updated") for case in cases_to_check]

            latest_hashes = {
                ir.ir_family.ir_family_id: ir.sha_hash
                for ir in latest_report_list
            }

            for case in cases_to_check:
                if case.json_hash != latest_hashes[case.request_id]:
                    cases_to_update.append(case)

        except GELInterpretationReport.DoesNotExist as e:
            # no such cases.
            pass

        return cases_to_update

    def add_cases(self):
        """
        Adds the cases to the database which required adding.
        """
        update_order = (
            # tuple of tuples to preserve update order. each sub-tuple is the
            # key to access the attribute manager and whether is has many objs
            (Clinician, False),
            (Family, False),
            (Phenotype, True),
            (Panel, True),
            (PanelVersion, True),
            (Gene, True),
            (Transcript, True),
            (Proband, False),
            (Relative, True),
            (InterpretationReportFamily, False),
            (GELInterpretationReport, False),
            (ToolOrAssemblyVersion, True),
            (Variant, True),
            (TranscriptVariant, True),
            (ProbandVariant, True),
            (ProbandTranscriptVariant, True),
            (ReportEvent, True)
        )

        if self.cases_to_add:
            # we need vep results for all cases, which needs to be done in batch
            variants = []
            case_id_map = {}
            for case in self.cases_to_add:
                # map case id to cases to easily assign transcripts from variant
                case_id_map[case.request_id] = case
                variants += case.variants

            # fetch the transcripts
            transcripts = generate_transcripts(variants)

            # assign transcripts
            i = 0
            while i < len(transcripts):  # keep going until no transcripts left
                transcript = transcripts.pop(0)
                case_id = transcript.case_id
                case = case_id_map[case_id]
                case.transcripts.append(transcript)

        # ------------------- #
        # BULK UPDATE PROCESS #
        # ------------------- #
        for model_type, many in update_order:
            for case in self.cases_to_add:
                # create a CaseAttributeManager for the case
                case.attribute_managers[model_type] = CaseAttributeManager(
                    case, model_type)
                # use thea attribute manager to set the case models
                attribute_manager = case.attribute_managers[model_type]
                attribute_manager.get_case_model()
            if not many:
                # get a list of CaseModels
                model_list = [
                    case.attribute_managers[model_type].case_model
                    for case in self.cases_to_add
                ]
            elif many:
                model_list = []
                for case in self.cases_to_add:
                    attribute_manager = case.attribute_managers[model_type]
                    many_case_model = attribute_manager.case_model
                    for case_model in many_case_model.case_models:
                        model_list.append(case_model)
            # now create the required new Model instances from CaseModel lists
            if model_type == GELInterpretationReport:
                # GEL_IR is a special case, preprocessing version no. means
                # Model.objects.bulk_create() is not available
                self.save_new(model_type, model_list)
            else:
                print("attempting to bulk create", model_type)
                self.bulk_create_new(model_type, model_list)
            # refresh CaseAttributeManagers with new CaseModels
            for model in model_list:
                if model.entry is False:
                    model.entry = model.check_found_in_db()

    def save_new(self, model_type, model_list):
        """
        Takes a list of CaseModel isntances of a given type, then saves any
        that are new into the database. This function is for models such as
        GELInterpretationReport which require preprocessing and so cannot be
        bulk created (which does not call the object.save() function)
        """
        # get the attribute dicts for ModelCases which have no database entry
        new_attributes = [
            case_model.model_attributes
            for case_model in model_list
            if case_model.entry is False]
        # use sets and tuples to remove duplicate dictionaries
        new_attributes = [
            dict(attribute_tuple)
            for attribute_tuple
            in set([
                tuple(attribute_dict.items())
                for attribute_dict
                in new_attributes])]
        pprint.pprint(new_attributes)
        # save database entries from the list of unique new attributes
        for attributes in new_attributes:
            model_type.objects.create(
                **attributes
            )

    def bulk_create_new(self, model_type, model_list):
        """
        Takes a list of CaseModel instances of a given model_type, then creates
        a list of unique attribute sets for that particular list of instances.
        This list of unique attributes can then be passed to a bulk_create
        function to update the database.
        """

        # get the attribute dicts for ModelCases which have no database entry
        new_attributes = [
            case_model.model_attributes
            for case_model in model_list
            if case_model.entry is False]
        # use sets and tuples to remove duplicate dictionaries
        new_attributes = [
            dict(attribute_tuple)
            for attribute_tuple
            in set([
                tuple(attribute_dict.items())
                for attribute_dict
                in new_attributes])]

        # bulk create database entries from the list of unique new attributes
        model_type.objects.bulk_create([
            model_type(**attributes)
            for attributes in new_attributes])

    def update_cases(self):
        """
        Updates the cases to the database which required updating.
        """
        pass
