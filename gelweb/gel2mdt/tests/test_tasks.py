import unittest
from django.test import TestCase
from ..tasks import *
from ..factories import *
from ..vep_utils.run_vep_batch import CaseVariant


class TestVariantAdder(TestCase):
    def setUp(self):
        self.family = FamilyFactory()
        self.proband = ProbandFactory(family=self.family)
        self.ir_family = InterpretationReportFamilyFactory(participant_family=self.family)
        self.gel_ir = GELInterpretationReportFactory(ir_family=self.ir_family)
        self.variant = VariantFactory()
        case_variant = CaseVariant(self.variant.chromosome,
                              self.variant.position,
                              self.gel_ir.id,
                              1,
                              self.variant.reference,
                              self.variant.alternate,
                              str(self.gel_ir.assembly))
        self.variant_adder = VariantAdder(report=self.gel_ir,
                                            variant=case_variant,
                                            variant_entry=self.variant)

    def test_variant_inserted(self):
        proband_variant = ProbandVariant.objects.filter(interpretation_report=self.gel_ir).first()
        assert proband_variant.variant == self.variant

class TestUpdateDemographics(TestCase):
    def setUp(self):
        #Need to add a case without demographics and then use this?
        pass

