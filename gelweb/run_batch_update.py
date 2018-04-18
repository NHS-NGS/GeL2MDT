from gel2mdt.database_utils.multiple_case_adder import MultipleCaseAdder

#mca = MultipleCaseAdder(sample_type='cancer', head=2, test_data=False, skip_demographics=True, pullt3=False)
#mca.update_database()
#del mca
mca = MultipleCaseAdder(sample_type='raredisease', head=30, test_data=False, skip_demographics=True, pullt3=False)
mca.update_database()
