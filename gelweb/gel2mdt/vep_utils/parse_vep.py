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
from pysam import VariantFile

class ParseVep:
    """
    Class of functions for parsing VEP annotated vcf files.
    Typically annotated using the following command:
        vep -i input_vcf -o output.vcf --cache --fork 4 --vcf --flag_pick --exclude_predicted --everything
        --dont_skip --total_length --offline --fasta
    Uses Pysam as a VCF parser - see URL below for detail:
    http://pysam.readthedocs.io/en/latest/usage.html#working-with-vcf-bcf-formatted-files
    """

    def get_fields(self, csq_info_string):
        """
        This function takes the CSQ info field from the header and breaks it up into a list.
        Input:
        csq_info_string = A string representing the CSQ field from the VCF header e.g.
        "##INFO=<ID=CSQ,Number=.,Type=String,Description='Consequence annotations from Ensembl VEP.
        Format: Allele|Consequence|IMPACT|SYMBOL'>"
        Output:
        csq_info_list = A list containing the annoatation titles from the Format : part of the csq_info_string e.g.
        ['Allele', 'Consequence', 'IMPACT', 'SYMBOL']
        """
        csq_info_string = csq_info_string.strip()
        index =  csq_info_string.index('Format:') +8
        csq_info_list = csq_info_string[index:len(csq_info_string)-2].split('|')
        return csq_info_list

    def get_variant_csq(self, variant_csq_string):
        """
        This function takes the CSQ field for a particular variant and breaks it up into a list.
        Input:
        variant_csq_string = A string containing the csq annotations within the vcf e.g.
        "A|B|C|D"
        Output:
        A list containing the variant_csq_string split up. e.g. [A, B, C, D]
        """
        return variant_csq_string.split('|')

    def create_csq_dict(self, field_list, variant_csq_list):
        """
        Combine the csq_info_list from the header and the csq data for a particular variant into a dictionary.
        Input:
        field_list = Output from get_fields()
        variant_csq_list = Output from get_variant_csq()
        Output:
        csq_dict = A dictionary combing the two inputs - field_list items are the keys.
        """
        zipped = zip(field_list, variant_csq_list)
        csq_dict = {}
        for info in zipped:
            csq_dict[info[0]] = info[1]
        return csq_dict

    def read_file(self, file):
        """
        Reads in a
        :param file: A VCF file that as been annotated with VEP
        :return: A list of dictionaries containing information about all the variants
        """
        vep_vcf = VariantFile(file)
        try:
            csq_fields = str(vep_vcf.header.info['CSQ'].record)
            csq_fields = self.get_fields(csq_fields)
        except:
            raise ValueError('Problem parsing CSQ header in vcf.')

        master_list = []

        for rec in vep_vcf.fetch():
            variant_data_dict = {}
            variant_data_dict['pos'] = rec.pos
            variant_data_dict['chrom'] = rec.chrom
            variant_data_dict['reference'] = rec.ref
            variant_data_dict['format'] = rec.format.keys()
            variant_data_dict['alt_alleles'] = rec.alts
            variant_data_dict['quality'] = rec.qual
            variant_data_dict['id'] = rec.id
            filter_status = rec.filter
            if len(filter_status.keys()) == 0:
                variant_data_dict['filter_status'] = "."
            else:
                variant_data_dict['filter_status'] = ";".join(filter_status.keys())
            for key in rec.info.keys():
                new_key = key.replace('.', '_')
                if key == 'CSQ':
                    csq_data = rec.info['CSQ']
                    all_transcript__dict = {}
                    for transcript in csq_data:
                        transcript_data = self.get_variant_csq(transcript)
                        transcript_dict = self.create_csq_dict(csq_fields, transcript_data)
                        transcript_name = transcript_dict['Feature']
                        all_transcript__dict[transcript_name] = transcript_dict
                    variant_data_dict['transcript_data'] = all_transcript__dict
                else:
                    variant_data_dict[new_key] = rec.info[key]
            master_list.append(variant_data_dict)
        return master_list