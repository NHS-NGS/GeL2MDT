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

from django.core.management.base import BaseCommand, CommandError
from gel2mdt.database_utils.multiple_case_adder import MultipleCaseAdder


class Command(BaseCommand):
    help = """Run the multiple case adder to update the database."""

    def add_arguments(self, parser):
        """Gather options for running the MultipleCaseAdder."""
        parser.add_argument('--test-data', action='store_true',
                            help='Use the test data jsons instead of polling'
                                 ' the GeL API.')
        parser.add_argument('--sample', default=None,
                            help='Specify a GeL ID to update a single sample.')
        parser.add_argument('--sample-type', default='raredisease',
                            help='Type of samples to retrieve. Default:'
                            ' raredisease', choices=['raredisease', 'cancer'])
        parser.add_argument('--case-count', default=None, type=int,
                            help='Number of cases to retrieve. If not supplied'
                            ' all cases will be retrieved.')
        parser.add_argument('--skip-demographics', action='store_true',
                            help='Skip calls to LabKey.')
        parser.add_argument('--pullt3', action='store_true',
                            help='Include the Tier 3 variants (this is time'
                            ' consuming!)')

    def handle(self, *args, **options):
        """Run the MultipleCaseAdder with the supplied options."""
        mca = MultipleCaseAdder(sample_type=options['sample_type'],
                                sample=options['sample'],
                                head=options['case_count'],
                                test_data=options['test_data'],
                                skip_demographics=options['skip_demographics'],
                                pullt3=options['pullt3'])
        mca.update_database()
