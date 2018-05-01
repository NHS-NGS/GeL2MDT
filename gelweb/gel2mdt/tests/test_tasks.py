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
