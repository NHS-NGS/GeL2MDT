import labkey as lk
from ..config import load_config


class DemographicsHandler:
    def __init__(self, sample_type):
        self.sample_type = sample_type

        self.config_dict = load_config.LoadConfig().load()
        if sample_type == 'raredisease':
            self.labkey_server_request_wlgmc = self.config_dict['labkey_server_request_wlgmc'] # wlgmc specific
            self.labkey_server_request_ntgmc = self.config_dict['labkey_server_request_ntgmc'] # ntgmc specific
        else:
            self.labkey_server_request_wlgmc = self.config_dict['labkey_cancer_server_request_wlgmc']
            self.labkey_server_request_ntgmc = self.config_dict['labkey_cancer_server_request_ntgmc']
        self.server_context_wlgmc = lk.utils.create_server_context(
            'gmc.genomicsengland.nhs.uk', self.labkey_server_request_wlgmc, '/labkey', use_ssl=True)
        self.server_context_ntgmc = lk.utils.create_server_context(
            'gmc.genomicsengland.nhs.uk', self.labkey_server_request_ntgmc, '/labkey', use_ssl=True)


    def get_demographics(self, participant_ids):
        server_context_list = [self.server_context_ntgmc, self.server_context_wlgmc]
        all_results = []

        if self.sample_type == 'raredisease':
            schema_name = 'gel_rare_diseases'
        else:
            schema_name = 'gel_cancer'
        
        for participant_id in participant_ids:
            query = participant_id
            labkey_url_index = 0
            all_gmc_labkeys_attempted = False
            participant_demographics = {}

            while not all_gmc_labkeys_attempted:
                # try most probable labkey url first
                results = lk.query.select_rows(
                    server_context=server_context_list[labkey_url_index],
                    schema_name=schema_name,
                    query_name='participant_identifier',
                    filter_array=[
                         lk.query.QueryFilter('participant_id', query, 'in')
                    ]
                )
                try:
                    participant_demographics["surname"] = results['rows'][0].get(
                            'surname')
                except IndexError as e:
                    pass

                if 'surname' in participant_demographics:
                    print("Found participant:", participant_id)
                    all_results.append(results['rows'][0])
                    all_gmc_labkeys_attempted = True # skip as other labkey url not required now
                else:
                    if labkey_url_index == 0:
                        print("Participant", participant_id, "demographics not found in labkey path:", server_context_list[labkey_url_index]._container_path)
                        labkey_url_index += 1
                        print("Searching within alternate labkey path:", server_context_list[labkey_url_index]._container_path)
                    else:
                        print("Cannot find", participant_id, "case demographics in labkey")
                        all_gmc_labkeys_attempted = True
                        pass

        return all_results


    def get_clinicians(self, family_ids):
        server_context_list = [self.server_context_ntgmc, self.server_context_wlgmc]
        all_results = []

        if self.sample_type == 'raredisease':
            schema_name = 'gel_rare_diseases'
            query_name = 'rare_diseases_registration'
            filter_type = 'family_id'
        else:
            schema_name = 'gel_cancer'
            query_name = 'cancer_registration'
            filter_type = 'participant_identifiers_id'

        for family_id in family_ids:
            query = family_id
            labkey_url_index = 0
            all_gmc_labkeys_attempted = False
            clinician_details = {}
            
            while not all_gmc_labkeys_attempted:
                # try most probable labkey url first
                results = lk.query.select_rows(
                    server_context=server_context_list[labkey_url_index],
                    schema_name=schema_name,
                    query_name=query_name,
                    filter_array=[
                        lk.query.QueryFilter(filter_type, query, 'contains')
                    ]
                )
                try:
                    clinician_details['name'] = results['rows'][0].get(
                        'consultant_details_full_name_of_responsible_consultant')
                except IndexError as e:
                    pass

                if 'name' in clinician_details:
                    print("Found clinician details for family_id:", family_id)
                    all_results.append(results['rows'][0])
                    all_gmc_labkeys_attempted = True # skip as other labkey url not required now
                else:
                    if labkey_url_index == 0:
                        print("Participant", family_id, "clinician not found in labkey path:", server_context_list[labkey_url_index]._container_path)
                        labkey_url_index += 1
                        print("Searching within alternate labkey path:", server_context_list[labkey_url_index]._container_path)
                    else:
                        print("Cannot find", family_id, "clinician in labkey")
                        all_gmc_labkeys_attempted = True
                        pass
        return all_results

     
    def get_diagnosis(self, participant_ids):
        # search in LabKey for recruited disease
        server_context_list = [self.server_context_ntgmc, self.server_context_wlgmc]
        all_results = []

        for participant_id in participant_ids:
            print(participant_id)
            labkey_url_index = 0
            all_gmc_labkeys_attempted = False
            diagnosis = {}

            if self.sample_type == 'raredisease':
                while not all_gmc_labkeys_attempted:
                    print(labkey_url_index)
                    query = participant_id
                    results = lk.query.select_rows(
                        server_context=server_context_list[labkey_url_index],
                        schema_name='gel_rare_diseases',
                        query_name='rare_diseases_diagnosis',
                        filter_array=[
                            lk.query.QueryFilter('participant_identifiers_id', query, 'in')
                        ]
                    )
                    try:
                        diagnosis['pid'] = results['rows'][0].get('participant_identifiers_id')
                    except IndexError as e:
                        pass

                    if 'pid' in diagnosis:
                        print("Found", participant_id)
                        all_results.append(results['rows'][0])
                        all_gmc_labkeys_attempted = True # skip as other labkey url not required now
                    else:
                        if labkey_url_index == 0:
                            print("Participant", participant_id, "diagnosis not found in labkey path:", server_context_list[labkey_url_index]._container_path)
                            labkey_url_index += 1
                            print("Searching within alternate labkey path:", server_context_list[labkey_url_index]._container_path)
                        else:
                            print("Cannot find", participant_id, "case diagnosis in any labkey")
                            all_gmc_labkeys_attempted = True
                            pass
        return all_results

