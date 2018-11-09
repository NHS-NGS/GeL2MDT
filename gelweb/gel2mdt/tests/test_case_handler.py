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
from gel2mdt.database_utils.multiple_case_adder import TranscriptManager, VariantManager, GeneManager, PanelManager
import json
from gel2mdt.database_utils.case_handler import Case
from protocols.reports_6_0_0 import InterpretedGenome, InterpretationRequestRD


class Test_Case(object):
    """
    Common operations on our test zoo.
    """
    def __init__(self):
        self.transcript_manager = TranscriptManager()
        self.variant_manager = VariantManager()
        self.gene_manager = GeneManager()
        self.panel_manager = PanelManager()
        self.case_json = json.load(open('gel2mdt/tests/test_files/v6_rd_example.json'))
        self.case = Case(
            case_json=self.case_json,
            panel_manager=self.panel_manager,
            variant_manager=self.variant_manager,
            gene_manager=self.gene_manager,
            skip_demographics=True,
            pullt3=True
        )
        self.ir_obj = InterpretationRequestRD.fromJsonDict(self.case_json['interpretation_request']['json_request'])

    def test_hash_json(self):
        assert self.case.hash_json() == '73ebff38fe57b0c2d227cbaacd5ce1f4fd24ec061700e788ba3ed11143e7de619ae3bcac' \
                                        '12960a5ec86ee149fd9c5eb9ad5d3f67c1661c69a6c0f84541310b2f'

    def test_get_family_members(self):
        assert self.case.get_family_members() == [{'gel_id': '115009625',
                                                   'relation_to_proband': 'Father',
                                                   'affection_status': True,
                                                   'sequenced': True,
                                                   'sex': 'MALE'},
                                                  {'gel_id': 'NR_115009585_2797550',
                                                   'relation_to_proband': 'PaternalGrandfather',
                                                   'affection_status': False,
                                                   'sequenced': False,
                                                   'sex': 'MALE'},
                                                  {'gel_id': 'NR_115009585_2797551',
                                                   'relation_to_proband': 'PaternalGrandmother',
                                                   'affection_status': False,
                                                   'sequenced': False,
                                                   'sex': 'FEMALE'},
                                                  {'gel_id': '115009609',
                                                   'relation_to_proband': 'Mother',
                                                   'affection_status': False,
                                                   'sequenced': True,
                                                   'sex': 'FEMALE'},
                                                  {'gel_id': 'NR_115009585_2797598',
                                                   'relation_to_proband': 'MaternalGrandfather',
                                                   'affection_status': False,
                                                   'sequenced': False,
                                                   'sex': 'MALE'},
                                                  {'gel_id': 'NR_115009585_2797599',
                                                   'relation_to_proband': 'MaternalGrandmother',
                                                   'affection_status': False,
                                                   'sequenced': False,
                                                   'sex': 'FEMALE'}]
