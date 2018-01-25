import unittest
from django.test import TestCase

from ..database_utils.multiple_case_adder import MultipleCaseAdder
from ..database_utils.case_handler import Case, CaseModel, ManyCaseModel
from ..models import *

import re
import os
import json
import hashlib
from datetime import datetime
from django.utils import timezone


class TestCaseOperations(object):
    """
    Common operations on our test zoo.
    """
    def __init__(self):
        self.file_path_list = [
            # get the list of absolute file paths for the cases in test_files
            os.path.join(
                os.getcwd(),
                "gel2mdt/tests/test_files/{filename}".format(
                    filename=filename)
            ) for filename in os.listdir(
                os.path.join(
                    os.getcwd(),
                    "gel2mdt/tests/test_files"
                )
            )
        ]

        self.json_list = [
            json.load(open(file_path)) for file_path in self.file_path_list
        ]

        self.request_id_list = [
            str(x["interpretation_request_id"]) + "-" + str(x["version"])
            for x in self.json_list]

        self.json_hashes = {
            str(x["interpretation_request_id"]) + "-" + str(x["version"]):
                hashlib.sha512(
                    json.dumps(x, sort_keys=True).encode('utf-8')
                ).hexdigest() for x in self.json_list
                }

    def get_case_mapping(self, multiple_case_adder):
        """
        Return a tuple mapping of case, test_case for all of the newly
        created cases.
        """
        test_cases = self.json_list
        cases = multiple_case_adder.list_of_cases
        case_mapping = []
        for case in cases:
            for test_case in test_cases:
                if case.request_id \
                    == str(test_case["interpretation_request_id"]) + "-" \
                        + str(test_case["version"]):
                    case_mapping.append(case, test_case)

    def add_cases_to_database(self, change_hash=False):
        """
        For all the cases we have stored, add them all to the database.
        :param change_hash: Default=False. If True, hashes will be changes for
        GELInterpretationReport entries so that test cases in MCA get flagged
        for update.
        """
        # make dummy related tables
        clinician = Clinician.objects.create(
            name="test_clinician",
            email="test@email.com",
            hospital="test_hospital"
        )
        family = Family.objects.create(
            clinician=clinician,
            gel_family_id=100
        )

        # convert our test data into IR and IRfamily model instances
        ir_family_instances = [InterpretationReportFamily(
            participant_family=family,
            cip=json["cip"],
            ir_family_id=str(json["interpretation_request_id"]) +
            "-" + str(json["version"]),
            priority=json["case_priority"]
        ) for json in self.json_list]
        InterpretationReportFamily.objects.bulk_create(ir_family_instances)

        ir_instances = [GELInterpretationReport(
            ir_family=InterpretationReportFamily.objects.get(
                ir_family_id=str(json["interpretation_request_id"]) +
                "-" + str(json["version"])),
            polled_at_datetime=timezone.make_aware(datetime.now()),
            sha_hash=self.get_hash(json, change_hash),
            status=json["status"][0]["status"],
            updated=json["status"][0]["created_at"],
            user=json["status"][0]["user"]
        ) for json in self.json_list]
        for ir in ir_instances:
            ir.save()

    def get_hash(self, json, change_hash):
        """
        Take a json and whether or not to change a hash, then return
        the hash of that json. Changing hash may be required if testing
        whether a case has mismatching hash values from the latest stored.
        """
        hash_digest = self.json_hashes[
            str(json["interpretation_request_id"]) +
            "-" + str(json["version"])]
        if change_hash:
            hash_digest = hash_digest[::-1]

        return hash_digest


class TestAddCases(TestCase):
    def setUp(self):
        """
        Instantiate a MultipleCaseAdder for the zoo of test cases.
        """
        self.case_update_handler = MultipleCaseAdder(test_data=True)

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
        test_cases = TestCaseOperations()
        for case in self.case_update_handler.list_of_cases:
            assert case.json_hash == test_cases.json_hashes[case.request_id]

    def test_extract_proband(self):
        """
        Test that we can get the proband out of the json as a dict-type.
        """
        test_cases = TestCaseOperations()
        case_mapping = test_cases.get_case_mapping(case_update_handler)

        for case, test_case in case_mapping:
            ir_data = test_case["interpretation_request_data"]["json_request"]
            particicpants = ir_data["pedigree"]["participants"]
            proband = None
            for participant in participants:
                if participant["isProband"]:
                    proband = participant
            assert case.proband["gelId"] == proband["gelId"]

    def test_extraxt_latest_status(self):
        """
        Test that the status extracted has the latest date and most progressed
        status of all the statuses.
        """
        test_cases = TestCaseOperations()


class TestIdentifyCases(TestCase):
    """
    Tests to ensure that MultipleCaseAdder can correctly determine
    which cases should be added, updated, and skipped.
    """
    def test_identify_cases_to_add(self):
        """
        MultipleCaseAdder recognises which cases need to be added.
        """
        case_update_handler = MultipleCaseAdder(test_data=True)
        test_cases = TestCaseOperations()

        for case in case_update_handler.cases_to_add:
            # all the test cases should be flagged as 'to add' since none added
            assert case.request_id in test_cases.request_id_list

        assert not case_update_handler.cases_to_update

    def test_identify_cases_to_update(self):
        """
        MultipleCaseAdder recognises hash differences to determine updates.
        """
        # add all of our test cases first. change hashes to trick MCA into
        # thinking the test files need to be updated in the database
        test_cases = TestCaseOperations()
        test_cases.add_cases_to_database(change_hash=True)

        # now cases are added, MCA should recognise this when checking
        case_update_handler = MultipleCaseAdder(test_data=True)

        to_update = case_update_handler.cases_to_update
        assert len(to_update) > 0
        for case in to_update:
            assert case.request_id in test_cases.request_id_list

    def test_identify_cases_to_skip(self):
        """
        MultipleCaseAdder recognises when latest version hashes match current.
        """
        test_cases = TestCaseOperations()
        # add all the test cases to db but retain hash so attempting to re-add
        # should cause a skip
        test_cases.add_cases_to_database()

        case_update_handler = MultipleCaseAdder(test_data=True)

        to_skip = case_update_handler.cases_to_skip
        assert len(to_skip) > 0
        for case in to_skip:
            assert case.request_id in test_cases.request_id_list


class TestCaseModel(TestCase):
    """
    Test functions carried out by the CaseModel class, ie. checking if an
    entry for a particular case needs to be added or is already present in
    the database.
    """
    def test_new_clinician(self):
        """
        Return created=False when a Clinician is not known to the db.
        """
        clinician = CaseModel(Clinician, {
            "name": "test",
            "email": "test",
            "hospital": "test"
        })
        assert clinician.entry is False  # checking for a literal False

    def test_existing_clinician(self):
        """
        Returns a clinician object when Clinician is known to the db.
        """
        clinician_attributes = {
            "name": "test",
            "email": "test",
            "hospital": "test"
        }
        archived_clinician = Clinician.objects.create(
            **clinician_attributes
        )

        test_clinician = CaseModel(Clinician, clinician_attributes)
        assert test_clinician.entry.id == archived_clinician.id


class TestAddCases(TestCase):
    """
    Test that a case has been faithfully added to the database along with
    all of the required related tables when needed.
    """
    def test_add_clinician(self):
        """
        Clinician has been fetched or added that matches the json
        """
        case_list_handler = MultipleCaseAdder(test_data=True)
        try:
            Clinician.objects.get(**{
                "name": "unknown",
                "email": "unknown",
                "hospital": "unknown"
            })
            created = True
        except Clinician.DoesNotExist as e:
            created = False
        assert created
        # now check that we are refreshing clinician in the case models:
        for case in case_list_handler.cases_to_add:
            assert case.clinician.entry is not False

    def test_add_family(self):
        case_list_handler = MultipleCaseAdder(test_data=True)
        test_cases = TestCaseOperations()
        try:
            for test_case in test_cases.json_list:
                Family.objects.get(
                    **{
                        "gel_family_id": int(test_case["family_id"])
                    }
                )
            created = True
        except Family.DoesNotExist as e:
            created = False
        assert created

    def test_add_phenotypes(self):
        """
        All phenotypes in json added with HPO & description.
        """
        case_list_handler = MultipleCaseAdder(test_data=True)
        test_cases = TestCaseOperations()

        for case in case_list_handler.cases_to_add:
            for phenotype in case.phenotypes.case_models:
                assert phenotype.entry is not False

    def test_associated_family_and_phenotypes(self):
        """
        Once phenotypes have been added, ensure M2M creation with Family.
        """
        pass

    def test_add_ir_family(self):
        """
        Family matching json data has been added/fetched
        """
        pass

    def test_add_or_get_panel_version(self):
        """
        Panel and panelversion from json added/fetched faithfully.
        """
        pass

    def test_add_or_get_panel_version_genes(self):
        """
        If panel version is new, check that genes corroborate with panelApp.
        """
        pass

    def test_add_ir_family(self):
        """
        Test that a new IRfamily has been made with a request ID matching the
        json.
        """
        pass

    def test_add_ir(self):
        """
        Test that a new IR has been made and links to the correct IRfamily.
        """
        pass
