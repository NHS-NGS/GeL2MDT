import labkey as lk
from ..config import load_config


class DemographicsHandler:
    def __init__(self, sample_type):
        self.sample_type = sample_type

        self.config_dict = load_config.LoadConfig().load()
        if sample_type == 'raredisease':
            self.labkey_server_request = self.config_dict['labkey_server_request']
        else:
            self.labkey_server_request = self.config_dict['labkey_cancer_server_request']
        self.server_context = lk.utils.create_server_context(
            'gmc.genomicsengland.nhs.uk', self.labkey_server_request, '/labkey', use_ssl=True)

    def get_demographics(self, participant_ids):
        if self.sample_type == 'raredisease':
            schema_name = 'gel_rare_diseases'
        else:
            schema_name = 'gel_cancer'
        query = ';'.join(participant_ids)
        results = lk.query.select_rows(
            server_context=self.server_context,
            schema_name=schema_name,
            query_name='participant_identifier',
            filter_array=[
                lk.query.QueryFilter('participant_id', query, 'in')
            ]
        )
        return results['rows']

    def get_clinicians(self, family_ids):
        if self.sample_type == 'raredisease':
            schema_name = 'gel_rare_diseases'
            query_name = 'rare_diseases_registration'
            filter_type = 'family_id'
        else:
            schema_name = 'gel_cancer'
            query_name = 'cancer_registration'
            filter_type = 'participant_identifiers_id'
        query = ';'.join(family_ids)
        results = lk.query.select_rows(
            server_context=self.server_context,
            schema_name=schema_name,
            query_name=query_name,
            filter_array=[
                lk.query.QueryFilter(filter_type, query, 'in')
            ]
        )
        return results['rows']

    def get_diagnosis(self, participant_ids):
        # search in LabKey for recruited disease
        if self.sample_type == 'raredisease':
            query = ';'.join(participant_ids)
            results = lk.query.select_rows(
                server_context=self.server_context,
                schema_name='gel_rare_diseases',
                query_name='rare_diseases_diagnosis',
                filter_array=[
                    lk.query.QueryFilter('participant_identifiers_id', query, 'in')
                ]
            )
            return results['rows']
