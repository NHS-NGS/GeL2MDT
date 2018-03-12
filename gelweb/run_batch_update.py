from gel2mdt.database_utils.multiple_case_adder import MultipleCaseAdder

mca = MultipleCaseAdder(test_data=True, skip_demographics=True)
mca.update_database()
