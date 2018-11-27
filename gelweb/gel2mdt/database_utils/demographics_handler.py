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

    def get_demographics_wl(self, participant_ids_wl):
        if self.sample_type == 'raredisease':
            schema_name = 'gel_rare_diseases'
        else:
            schema_name = 'gel_cancer'

        query = ';'.join(participant_ids_wl)
        results = lk.query.select_rows(
            server_context=self.server_context_wlgmc,
            schema_name=schema_name,
            query_name='participant_identifier',
            filter_array=[
                 lk.query.QueryFilter('participant_id', query, 'in')
            ]
        )
        return results['rows']

    def get_demographics_nt(self, participant_ids_nt):
        if self.sample_type == 'raredisease':
            schema_name = 'gel_rare_diseases'
        else:
            schema_name = 'gel_cancer'

        query = ';'.join(participant_ids_nt)
        results = lk.query.select_rows(
            server_context=self.server_context_ntgmc,
            schema_name=schema_name,
            query_name='participant_identifier',
            filter_array=[
                 lk.query.QueryFilter('participant_id', query, 'in')
            ]
        )
        return results['rows']


    def get_clinicians_wl(self, family_ids_wl):
        if self.sample_type == 'raredisease':
            schema_name = 'gel_rare_diseases'
            query_name = 'rare_diseases_registration'
            filter_type = 'family_id'
        else:
            schema_name = 'gel_cancer'
            query_name = 'cancer_registration'
            filter_type = 'participant_identifiers_id'
        query = ';'.join(family_ids_wl)
        results = lk.query.select_rows(
            server_context=self.server_context_wlgmc,
            schema_name=schema_name,
            query_name=query_name,
            filter_array=[
                lk.query.QueryFilter(filter_type, query, 'in')
            ]
        )
        return results['rows']


    def get_clinicians_nt(self, family_ids_nt):
        if self.sample_type == 'raredisease':
            schema_name = 'gel_rare_diseases'
            query_name = 'rare_diseases_registration'
            filter_type = 'family_id'
        else:
            schema_name = 'gel_cancer'
            query_name = 'cancer_registration'
            filter_type = 'participant_identifiers_id'
        query = ';'.join(family_ids_nt)
        results = lk.query.select_rows(
            server_context=self.server_context_ntgmc,
            schema_name=schema_name,
            query_name=query_name,
            filter_array=[
                lk.query.QueryFilter(filter_type, query, 'in')
            ]
        )
        return results['rows']      

    def get_diagnosis_wl(self, participant_ids_wl):
        # search in LabKey for recruited disease
        if self.sample_type == 'raredisease':
            query = ';'.join(participant_ids_wl)
            results = lk.query.select_rows(
                server_context=self.server_context_wlgmc,
                schema_name='gel_rare_diseases',
                query_name='rare_diseases_diagnosis',
                filter_array=[
                    lk.query.QueryFilter('participant_identifiers_id', query, 'in')
                ]
            )
        return results['rows']

    def get_diagnosis_nt(self, participant_ids_nt):
        # search in LabKey for recruited disease
        if self.sample_type == 'raredisease':
            query = ';'.join(participant_ids_nt)
            results = lk.query.select_rows(
                server_context=self.server_context_ntgmc,
                schema_name='gel_rare_diseases',
                query_name='rare_diseases_diagnosis',
                filter_array=[
                    lk.query.QueryFilter('participant_identifiers_id', query, 'in')
                ]
            )
        return results['rows']
