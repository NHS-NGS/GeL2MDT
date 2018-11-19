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
import os
import traceback
import json

from ..models import *
from ..api_utils.poll_api import PollAPI
from ..api_utils.cip_utils import InterpretationList
from ..vep_utils.run_vep_batch import generate_transcripts
from .case_handler import Case, CaseAttributeManager
from ..config import load_config
import pprint
import logging
import time
from .demographics_handler import DemographicsHandler
from tqdm import tqdm

# set up logging
logger = logging.getLogger(__name__)


class MultipleCaseAdder(object):
    """
    Representation of the process of adding many cases to the database.
    This class will handle the checking of cases already present, adding
    required related instances to the database and reporting status and
    errors during the process.
    """
    def __init__(self, sample_type, head=None, test_data=False,
                 skip_demographics=False, sample=None, pullt3=True,
                 bins=None):
        """
        Initiliase an instance of a MultipleCaseAdder to start managing
        a database update. This will get the list of cases available to
        us, hash them all, check which need to be added/updated and then
        manage the updating of the database.
        :param test_data: Boolean. Use test data or not. Default = False
        :param sample: If you want to add a single sample, set this the GELID
        :param pullt3: Boolean to pull t3 variants
        """
        print("Initialising a MultipleCaseAdder.")

        if sample_type == "cancer" or sample_type == "raredisease":
            pass
        else:
            raise ValueError('{sample_type} is not a valid entry for "sample_type"; please enter either "raredisease" or "cancer".'.format(sample_type=sample_type))

        # fetch and identify cases to add or update
        # -----------------------------------------
        # are we using test data files? defaults False (no)
        self.test_data = test_data
        # are we polling labkey? defaults False (yes)
        self.skip_demographics = skip_demographics
        # are we only getting a certain number of cases? defaults None (no)
        self.head = head
        self.pullt3 = pullt3
        # get the config file for datadumps
        self.config = load_config.LoadConfig().load()

        # instantiate a PanelManager for the Case classes to use
        self.panel_manager = PanelManager()
        self.transcript_manager = TranscriptManager()
        self.variant_manager = VariantManager()
        self.gene_manager = GeneManager()
        self.sample_type = sample_type

        if self.test_data:
            print("Fetching test data.")
            # set list_of_cases to test zoo
            self.list_of_cases = self.fetch_test_data()
            self.cases_to_poll = None
            print("Fetched test data.")
            self.cases_to_add = self.check_cases_to_add()
            self.cases_to_update = self.check_cases_to_update()  #
            self.cases_to_skip = set(self.list_of_cases) - \
                                 set(self.cases_to_add) - \
                                 set(self.cases_to_update)
            self.update_database()
        elif sample:
            interpretation_list_poll = InterpretationList(sample_type=sample_type, sample=sample)
            self.cases_to_poll = interpretation_list_poll.cases_to_poll
            self.list_of_cases = self.fetch_api_data()
            self.cases_to_update = self.list_of_cases
            print(self.cases_to_update)
            self.cases_to_add = []
            self.cases_to_skip = []
            self.update_database()
        else:
            # set list_of_cases to cases of interest from API
            print("Fetching live API data.")
            print("Polling for list of available cases...")
            interpretation_list_poll = InterpretationList(sample_type=sample_type)
            cases_fetched = len(interpretation_list_poll.cases_to_poll)
            print("Fetched", cases_fetched, "available cases")

            print("Determining which cases to poll...")
            # reverse update, do the newest first!
            self.total_cases_to_poll = interpretation_list_poll.cases_to_poll[::-1]
            if head:
                self.total_cases_to_poll = self.total_cases_to_poll[:head]
            self.num_cases_to_poll = len(self.total_cases_to_poll)

            if bins:
                bin_size = int(bins)
                print("bin size", bin_size)
                # work out how many hundreds in fetched cases
                num_full_bins = self.num_cases_to_poll // bin_size

                bin_ranges = []
                for i in range(num_full_bins):
                    bin_ranges.append(
                        [
                            (bin_size * i),            # e.g 0, 100
                            (bin_size * i) + bin_size  # e.g 100, 200 - SLICE so not inclusive
                        ]
                    )   # [0, 100], [100, 200] etc
                bin_ranges.append([num_full_bins * bin_size, None])
                print("bin ranges", bin_ranges)

                bin_count = 1
                for b in bin_ranges:
                    print("Fetching cases", b[0], "to", b[1], "(bin", bin_count, "of", str(len(bin_ranges)) + ")")
                    self.cases_to_poll = self.total_cases_to_poll[b[0]: b[1]]

                    print("Fetching API JSON data for cases to poll...")
                    self.list_of_cases = self.fetch_api_data()
                    if head:
                        # take a certain number of cases off the top
                        self.list_of_cases = self.list_of_cases[:head]
                    print("Fetched all required CIP API data.")
                    print("Checking which cases to add.")
                    self.cases_to_add = self.check_cases_to_add()
                    print("Checking which cases require updating.")
                    self.cases_to_update = self.check_cases_to_update()
                    self.cases_to_skip = set(self.list_of_cases) - \
                        set(self.cases_to_add) - \
                        set(self.cases_to_update)
                    self.update_database()

                    for case in self.cases_to_add:
                        del case
                    for case in self.cases_to_update:
                        del case

                    bin_count += 1

            else:
                # no bins, update as normal
                print("Fetching all cases.")
                self.cases_to_poll = self.total_cases_to_poll
                print("Fetching API JSON data for cases to poll...")
                self.list_of_cases = self.fetch_api_data()
                if head:
                    # take a certain number of cases off the top
                    self.list_of_cases = self.list_of_cases[:head]
                print("Fetched all required CIP API data.")
                print("Checking which cases to add.")
                self.cases_to_add = self.check_cases_to_add()
                print("Checking which cases require updating.")
                self.cases_to_update = self.check_cases_to_update()
                self.cases_to_skip = set(self.list_of_cases) - \
                    set(self.cases_to_add) - \
                    set(self.cases_to_update)
                self.update_database()

    def update_database(self):
        # begin update process
        # --------------------
        error = None
        added_cases = []
        updated_cases = []
        try:
            logger.info("Adding cases from cases_to_add.")
            print("Adding", len(self.cases_to_add), "cases")
            added_cases = self.add_cases()
            print("Updating", len(self.cases_to_update), "cases")
            updated_cases = self.add_cases(update=True)
            success = True
        except Exception as e:
            print("Encountered error:", e)
            error = traceback.format_exc()
            print(error)
            success = False
        finally:
            print("Recording update")
            # record the update in ListUpdate
            listupdate = ListUpdate.objects.create(
                update_time=timezone.now(),
                success=success,
                cases_added=len(self.cases_to_add),
                cases_updated=len(self.cases_to_update),
                sample_type=self.sample_type,
                error=error
            )
            listupdate.reports_added.add(*added_cases)
            listupdate.reports_updated.add(*updated_cases)

            # Add in case alert

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
            if filename.endswith('.json'):
                logger.info("Found case json at " + file_path + " for testing.")
                with open(file_path) as json_file:
                    json_data = json.load(json_file)
                    if json_data['sample_type'] == self.sample_type:
                        list_of_cases.append(Case(
                            case_json=json_data,
                            panel_manager=self.panel_manager,
                            variant_manager=self.variant_manager,
                            gene_manager=self.gene_manager,
                            skip_demographics=self.skip_demographics,
                            pullt3=self.pullt3))
        logger.info("Found " + str(len(list_of_cases)) +  " test cases.")
        return list_of_cases

    def fetch_api_data(self):
        list_of_cases = []
        # list comprehension, calling self.get_case_json each time for poll
        for case in tqdm(self.cases_to_poll):
            tqdm.write("Polling for: {case}".format(case=case["interpretation_request_id"]))

            c = Case(
                # instatiate a new case with the polled json
                case_json=self.get_case_json(case["interpretation_request_id"]),
                panel_manager=self.panel_manager,
                variant_manager=self.variant_manager,
                gene_manager=self.gene_manager,
                skip_demographics=self.skip_demographics,
                pullt3=self.pullt3
            )
            list_of_cases.append(c)

        print("Successfully fetched", len(list_of_cases), "cases from CIP API.")
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
        response = request_poll.get_json_response()
        return response

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
            if case.request_id not in list(database_cases):
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
        all_latest_reports = GELInterpretationReport.objects.latest_cases_by_sample_type(sample_type=self.sample_type)
        try:
            latest_report_list = []
            for case in cases_to_check:
                for report in all_latest_reports:
                    if case.request_id == report.ir_family.ir_family_id:
                        latest_report_list.append(report)

            latest_hashes = {
                ir.ir_family.ir_family_id: ir.sha_hash
                for ir in latest_report_list
            }

            for case in cases_to_check:
                latest_hash = latest_hashes.get(case.request_id, None)
                if not latest_hash or case.json_hash != latest_hash:
                    cases_to_update.append(case)

        except GELInterpretationReport.DoesNotExist as e:
            # no such cases.
            pass

        return cases_to_update

    def add_cases(self, update=False):
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
            (ToolOrAssemblyVersion, True),
            (Transcript, True),
            (Variant, True),
            (Proband, False),
            (Relative, True),
            (InterpretationReportFamily, False),
            (InterpretationReportFamilyPanel, True),
            (GELInterpretationReport, False),
            (ProbandVariant, True),
            (PVFlag, True),
            (TranscriptVariant, True),
            (ProbandTranscriptVariant, True),
            #(ReportEvent, True)
        )

        if update:
            cases = self.cases_to_update
        elif not update:
            cases = self.cases_to_add
        if cases:
            # we need vep results for all cases, which needs to be done in batch
            variants = []
            case_id_map = {}
            for case in cases:
                # map case id to cases to easily assign transcripts from variant
                case_id_map[case.request_id] = case
                variants += case.variants

            # fetch the transcripts and put them into TranscriptManager
            transcripts = generate_transcripts(variants)
            for transcript in transcripts:
                case_id = transcript.case_id
                case = case_id_map[case_id]
                self.transcript_manager.add_transcript(transcript, case.tools_and_versions['genome_build'] )

            # assign transcripts
            i = 0
            while i < len(transcripts):  # keep going until no transcripts left
                transcript = transcripts.pop(0) # check to see if transcript already exists in transcript manager
                case_id = transcript.case_id
                case = case_id_map[case_id]
                fetched_transcript = self.transcript_manager.fetch_transcript(transcript)
                # Reassigning case details
                transcript.transcript_canonical = fetched_transcript.transcript_canonical
                transcript.gene_model = fetched_transcript.gene_model
                # Append to case transcripts
                case.transcripts.append(transcript)

            # Labkey lookup for all cases
            if not self.skip_demographics:
                family_ids = []
                family_ids_nt = []
                family_ids_wl = []
                participant_ids = []
                participant_ids_nt = [] # wl_list
                participant_ids_wl = [] # nt_list

                demographic_handler = DemographicsHandler(self.sample_type)
                if self.sample_type == 'raredisease':
                    for case in cases:
                        family_ids.append(case.json["family_id"])
                        participant_ids.append(case.json["proband"])
                        for family_member in case.family_members:
                            participant_ids.append(family_member['gel_id'])

                    # rd pids 115* (nt) and 120* (wl) & ca 215* (nt) 220* (wl)
                    # fyi, format of participant_id if no result recorded in LabKey=NR_120000299_1233951
                    for participant_id in participant_ids:
                        if participant_id.startswith("NR_"):
                            pass # ignore
                        elif participant_id.startswith("115"):
                            participant_ids_nt.append(participant_id)
                        elif participant_id.startswith("120"):
                            participant_ids_wl.append(participant_id)

                    for family_id in family_ids:
                        if participant_id.startswith("NR_"):
                            pass # ignore
                        elif family_id.startswith("115"):
                            family_id_nt.append(family_id)
                        elif family_id.startswith("120"):
                            family_id_wl.append(family_id)
                    
                    # temp printing to file
                    # raw pid list
                    output_path = os.path.abspath('/root/gel2mdt/gelweb/')
                    pid_file_output = os.path.join(output_path, 'participant_ids.txt')
                    with open(pid_file_output,'w') as f:                      
                        for item in participant_ids:
                            f.write(item)
                            f.write('\n')

                    # nt list
                    output_path = os.path.abspath('/root/gel2mdt/gelweb/')
                    pid_file_output = os.path.join(output_path, 'participant_ids_nt.txt')
                    with open(pid_file_output,'w') as f:                      
                        for item in participant_ids_nt:
                            f.write(item)
                            f.write('\n')

                    # wl list
                    output_path = os.path.abspath('/root/gel2mdt/gelweb/')
                    pid_file_output = os.path.join(output_path, 'participant_ids_wl.txt')
                    with open(pid_file_output,'w') as f:                      
                        for item in participant_ids_wl:
                            f.write(item)
                            f.write('\n')

                    demographics = demographic_handler.get_demographics_wl(participant_ids_wl) # separate gmc split lists
                    demographics = demographic_handler.get_demographics_nt(participant_ids_nt)                   
                    clinicians = demographic_handler.get_clinicians_wl(family_ids_wl)
                    clinicians = demographic_handler.get_clinicians_nt(family_ids_nt)                    
                    diagnosis = demographic_handler.get_diagnosis_wl(participant_ids_wl)
                    diagnosis = demographic_handler.get_diagnosis_nt(participant_ids_nt)

                elif self.sample_type == 'cancer':
                    for case in cases:
                        participant_ids.append(case.json["proband"])
                        for family_member in case.family_members:  # Shouldn't be any but just for futureproofing!
                            participant_ids.append(family_member['gel_id'])

                    # fyi, format of participant_id if no result recorded in LabKey=NR_120000299_1233951
                    for participant_id in participant_ids:
                        if participant_id.startswith("NR_"):
                            pass # ignore
                        elif participant_id.startswith("215"):
                            participant_ids_nt.append(participant_id)
                        elif participant_id.startswith("220"):
                            participant_ids_wl.append(participant_id)

                    demographics = demographic_handler.get_demographics_wl(participant_ids_wl) # separate gmc split lists
                    demographics = demographic_handler.get_demographics_nt(participant_ids_nt) # adding gmc split lists                    
                    clinicians = demographic_handler.get_clinicians_wl(participant_ids_wl)
                    clinicians = demographic_handler.get_clinicians_nt(participant_ids_nt)                                   
                    diagnosis = None

                for case in cases:
                    case.demographics = demographics
                    case.clinicians = clinicians
                    case.diagnosis = diagnosis

        # ------------------- #
        # BULK UPDATE PROCESS #
        # ------------------- #
        for model_type, many in update_order:

            # prefetch database entries for check_found_in_db()
            lookups = self.get_prefetch_lookups(model_type)
            if lookups:
                model_objects = model_type.objects.all().values(*lookups)
            elif not lookups:
                model_objects = model_type.objects.all()
            for case in tqdm(cases, desc="Parsing {model_type} into DB".format(model_type=model_type.__name__)):
                # create a CaseAttributeManager for the case
                tqdm.write(case.request_id)
                case.attribute_managers[model_type] = CaseAttributeManager(
                    case, model_type, model_objects)
                # use thea attribute manager to set the case models
                attribute_manager = case.attribute_managers[model_type]
                attribute_manager.get_case_model()

            if not many:
                # get a list of CaseModels
                model_list = [
                    case.attribute_managers[model_type].case_model
                    for case in cases
                ]
            elif many:
                model_list = []
                for case in tqdm(cases, desc="Parsing {model_type} into DB".format(model_type=model_type.__name__)):
                    tqdm.write(case.request_id)
                    attribute_manager = case.attribute_managers[model_type]
                    many_case_model = attribute_manager.case_model
                    for case_model in tqdm(many_case_model.case_models, desc=case.request_id):
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
            lookups = self.get_prefetch_lookups(model_type)
            if lookups:
                model_objects = model_type.objects.all().values(*lookups)
            elif not lookups:
                model_objects = model_type.objects.all()
            for model in model_list:
                if model.entry is False:
                    model.check_found_in_db(model_objects)

        # finally, save jsons to disk storage
        cip_api_storage = self.config['cip_api_storage']
        case_reports = []
        for case in cases:
            ir_family = case.attribute_managers[InterpretationReportFamily].case_model.entry
            latest_case = GELInterpretationReport.objects.filter(
                ir_family=ir_family
            ).latest('polled_at_datetime')
            case_reports.append(latest_case)

            with open(
                    os.path.join(
                        cip_api_storage,
                        '{}.json'.format(
                            case.request_id + "-" + str(latest_case.archived_version)
                        )), 'w') as f:
                json.dump(case.raw_json, f)
        return case_reports


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
        # save database entries from the list of unique new attributes


        for attributes in new_attributes:
            obj = model_type(**attributes)
            obj.save()

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


        model_type.objects.bulk_create([
            model_type(**attributes)
            for attributes in new_attributes])

    def get_prefetch_lookups(self, model_type):
        """
        Takes a model type and returns list of the ForeignKey fields which
        need to be passed to prefetch_related() when creating a QuerySet to
        quickly get related items.

        When adding new tables to the database, add their FKs here.
        """
        lookup_dict = {
            Clinician: ['id','name', 'hospital', 'email'],
            Phenotype: ['id','hpo_terms'],
            Family: ['id',"gel_family_id"],
            FamilyPhenotype: ['id',"family", "phenotype"],
            Gene: ['id','hgnc_id'],
            Panel: ['id','panelapp_id'],
            PanelVersion: ['id',"panel", 'version_number'],
            PanelVersionGene: ['id',"panel_version", "gene"],
            ToolOrAssemblyVersion: ['id','tool_name','version_number'],
            InterpretationReportFamily: ['id',"ir_family_id"],
            InterpretationReportFamilyPanel: ['id',"ir_family", "panel"],
            GELInterpretationReport: ['id',"sha_hash"],
            Proband: ['id',"gel_id"],
            Relative: ['id',"gel_id", "proband"],
            Variant: ['id','chromosome', 'position', 'reference', 'alternate', "genome_assembly"],
            Transcript: ['id',"name", 'genome_assembly'],
            TranscriptVariant: ['id',"transcript", "variant"],
            ProbandVariant: ['id',"variant", "interpretation_report", 'max_tier'],
            PVFlag: ['id', "proband_variant", "flag_name"],
            ProbandTranscriptVariant: ['id',"transcript", "proband_variant"],
            ReportEvent: ['id',"proband_variant", "re_id"],
        }
        return lookup_dict[model_type]

    def update_cases(self):
        """
        Updates the cases to the database which required updating.
        """
        pass

class TranscriptManager(object):
    """
    A class which manages transcripts and avoids conflicts in
    duplicate CaseTranscripts
    """
    def __init__(self):
        self.fetched_transcripts = {} # should be {[name][build]}: CaseTranscript}

    def add_transcript(self, transcript, genome_build):
        if transcript.transcript_name not in self.fetched_transcripts:
            self.fetched_transcripts[transcript.transcript_name] = transcript
        else:
            if genome_build == 'GRCh38':
                self.fetched_transcripts[transcript.transcript_name] = transcript

    def fetch_transcript(self, transcript):
        return self.fetched_transcripts[transcript.transcript_name]


class GeneManager(object):

    def __init__(self):
        self.fetched_genes = {}
        self.searched_genes = {}
        self.config_dict = load_config.LoadConfig().load()

    def add_gene(self, gene):
        if gene['HGNC_ID'] not in self.fetched_genes:
            self.fetched_genes[gene['HGNC_ID']] = gene

    def fetch_gene(self, gene):
        return self.fetched_genes.get(gene['HGNC_ID'], None)

    def add_searched(self, ensembl_id, hgnc_id):
        self.searched_genes[ensembl_id] = hgnc_id

    def fetch_searched(self, ensembl_id):
        return self.searched_genes.get(ensembl_id, None)

    def write_genes(self):
        output = open(os.path.join(self.config_dict['gene_storage'], 'saved_genes.tsv'), 'w')
        for key in self.searched_genes:
            output.write(f'{key}\t{self.searched_genes[key]}\n')
        output.close()

    def load_genes(self):
        if os.path.isfile(os.path.join(self.config_dict['gene_storage'], 'saved_genes.tsv')):
            with open(os.path.join(self.config_dict['gene_storage'], 'saved_genes.tsv')) as f:
                for line in f:
                    word = line.rstrip().split('\t')
                    if len(word) > 1:
                        self.searched_genes[word[0]] = word[1]

class VariantManager(object):

    def __init__(self):
        self.fetched_variants = {}

    def add_variant(self, variant):
        '''
        Allows the addition and retrival of variants
        :param variant: Dict of Variant attributes
        :return:
        '''
        if (variant['chromosome'],
                               variant["position"],
                               variant["reference"],
                               variant["alternate"],
                               variant['genome_assembly']) not in self.fetched_variants:
            self.fetched_variants[(variant['chromosome'],
                               variant["position"],
                               variant["reference"],
                               variant["alternate"],
                               variant['genome_assembly'])] = variant

    def fetch_variant(self, variant):
        return self.fetched_variants.get((variant['chromosome'],
                                           variant["position"],
                                           variant["reference"],
                                           variant["alternate"],
                                          variant['genome_assembly']), None)

class PanelManager(object):
    """
    A class which manages the panels polled in the cases to avoid polling the
    same panel multiple times. Invokes PanelResposne classes for each different
    panel.
    """
    def __init__(self):
        self.fetched_panels = {}  # should be {(id, version): PanelResponse}
        self.panel_names = {}

    def add_panel_response(self, panelapp_id, panel_version, panelapp_response):
        """
        Instantiate a new PanelResponse and add it to fetched panels. Returns
        the added PanelResponse instance.
        """
        if panelapp_id not in self.fetched_panels:
            self.fetched_panels[panelapp_id] = {}
            self.panel_names[panelapp_id] = {'SpecificDiseaseName': panelapp_response['SpecificDiseaseName'],
                                             'DiseaseGroup': panelapp_response['DiseaseGroup'],
                                             'DiseaseSubGroup': panelapp_response['DiseaseSubGroup']}
        self.fetched_panels[panelapp_id][panel_version] = PanelResponse(
                panelapp_response=panelapp_response
        )

        return self.fetched_panels[panelapp_id][panel_version]

    def fetch_panel_response(self, panelapp_id, panel_version):
        """
        Take a panelApp ID and version number. If a corresponding panel is in
        fetched_panels then return it, otherwise return False.
        """
        pm_response = self.fetched_panels.get(panelapp_id, None)
        if pm_response:
            pm_response = self.fetched_panels[panelapp_id].get(panel_version, None)
        return pm_response

    def fetch_panel_names(self, panelapp_id):
        return self.panel_names.get(panelapp_id, None)



class PanelResponse(object):
    """
    Class to hold the json response from a panel as well as its panelApp ID and
    version number.
    """
    def __init__(self, panelapp_response):
        self.results = panelapp_response
