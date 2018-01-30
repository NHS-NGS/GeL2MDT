from ..database_utils import multiple_case_adder
from ..models import *
from .test_multiple_case_adder import TestCaseOperations
from datetime import datetime

def create_dummy_sample():
    """
    Fills the database with dummy data for the json from bwh
    :return:
    """
    # Initialising with ir_family and ir_instance
    Family.objects.filter(gel_family_id=100).delete()
    multiple_case_adder.MultipleCaseAdder(test_data=True)
    # Family.objects.filter(gel_family_id=100).delete()  # Have to delete previous version
    # test_cases = TestCaseOperations()
    # test_cases.add_cases_to_database()
    #
    # json = test_cases.json_list[0]
    #
    # family = Family.objects.get(gel_family_id=100)
    # ir_family_instance = InterpretationReportFamily.objects.get(ir_family_id=str(json["interpretation_request_id"]) +
    #         "-" + str(json["version"]))
    # ir_instance = GELInterpretationReport.objects.get(ir_family=ir_family_instance)
    #
    # proband_instance = Proband(gel_id=json['proband'],
    #                            family=family,
    #                            nhs_number=13872837,
    #                            lab_number=8312718,
    #                            forename='Sam',
    #                            surname='Smith',
    #                            date_of_birth=datetime.now(),
    #                            sex='M',
    #                            gmc='GOSH'
    #                            )
    # proband_instance.save()
    #
    # toolorassembly_instance = ToolOrAssembly(tool_name=json['assembly'],
    #                                          reference_link='http://grch37.ensembl.org/')
    # toolorassembly_instance.save()
    #
    # toolorassemblyversion_instance = ToolOrAssemblyVersion(tool=toolorassembly_instance,
    #                                                        version_number=1)
    # toolorassemblyversion_instance.save()
    #
    # # Need to add a panel, gene, phenotype
    #
    # # So to add a variant, I have to add a Variant, then add ProbandVariant, then add ReportEvent
    # for tieredvariant in json['interpretation_request_data']['json_request']['TieredVariants']:
    #     variant_instance = Variant(chromosome=tieredvariant['chromosome'],
    #                                position=tieredvariant['position'],
    #                                reference=tieredvariant['reference'],
    #                                alternate=tieredvariant['alternate'],
    #                                db_snp_id=tieredvariant['dbSNPid'],
    #                                genome_assembly=toolorassemblyversion_instance)
    #     variant_instance.save()
    #     probandvariant_instance = ProbandVariant(variant=variant_instance,
    #                                              interpretation_report=ir_instance,
    #                                              tools=toolorassemblyversion_instance)
    #     probandvariant_instance.save()
    #     reportevent_instances = []
    #     for reportevent in tieredvariant['reportEvents']:
    #         pass
    #         # reportevent_instances.append(ReportEvent(re_id=reportevent['reportEventId'],
    #         #                                          tier=reportevent['tier'],
    #         #                                          proband_variant=probandvariant_instance,
    #         #                                          panel=))


