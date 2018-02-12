#! /usr/bin/python

import primer3
from pybedtools import BedTool
from ..config import load_config


class InputSequence:
    """
    InputSequence instances initalised with the ID and sequence extracted from NCBI using the supplied NG number.
    Other instance variables record information about genomic location and a list of all SNPs (version 147) within
    the region in bed format. This list is used to mask common SNPs when desgining primers and for identifying other
    primer site SNPs.
    A list of all exons in the gene are stored and from these a list of target regions are determined.
    """

    def __init__(self, refseq_id, sequence, **kwargs):
        self.refseq_id = refseq_id
        self.sequence = sequence
        self.sequence_length = len(sequence)
        self.gene_name = ""
        self.chrom_number = None
        self.genomic_coords = None
        self.strand = None
        self.snps_bed = None
        self.exons = []
        self.target_regions = []
        for key, value in kwargs.items():
            setattr(self, key, value)

    def set_snps_bed(self, genome_build):
        """
        Uses the genomicCoords of the inputSequence to determine which SNPs are within
        range. The function searches through all SNPs and creates a bed file of the SNPs which are in range.

        NB: SNP tracks of all SNPs(147) have been downloaded from UCSC for each chromosome
        and stored in the genome/SNPs folder. (GRCh37)
        """
        start = self.genomic_coords[0]
        stop = self.genomic_coords[1]
        config_dict = load_config.LoadConfig().load()
        if '19' in genome_build or '37' in genome_build:
            snps = BedTool(config_dict['primer_hg19_snps_path_p1'] +
                           self.chrom_number + config_dict['primer_hg19_snps_path_p2'])
        elif '38' in genome_build:
            snps = BedTool(config_dict['primer_hg38_snps_path_p1'] +
                           self.chrom_number + config_dict['primer_hg38_snps_path_p2'])
        target_region = BedTool(
            self.chrom_number + " " + str(start) + " " + str(stop), from_string=True)
        self.snps_bed = snps.intersect(target_region)


class TargetRegion:
    """
    Stores information about the target regions. These may be whole exons, multiple exons, or parts of exons depending
    on their size. A masked sequence is created which masks the orginial sequence in the locations where common SNPs
    are found. These will then be avoided by the Primer3 API when designing the primers.
    """

    def __init__(self, target_id, sequence, seq_start, seq_stop, overhang, input_seq):
        self.target_id = target_id
        self.sequence = sequence
        self.seq_start = seq_start
        self.seq_stop = seq_stop
        self.overhang = overhang
        self.input_sequence = input_seq
        self.snps = []
        self.masked_sequence = ""
        self.primers = []

    def set_snps(self):
        """
        Uses the SNP bed file that was created to cover the whole input sequence to search for SNPs which are in
        range of the target region. This saves searching through the whole list of chromosome SNPs for each target
        region. A Snp object is created for each SNP found within range of the target region.
        """
        strand = self.input_sequence.strand
        chromosome_number = self.input_sequence.chrom_number
        input_seq_snps = self.input_sequence.snps_bed
        if strand == "+":
            start = self.seq_start
            stop = self.seq_stop
        else:
            start = self.seq_stop
            stop = self.seq_start
        snps_in_range = []
        target_region = BedTool(
            chromosome_number + " " + str(start) + " " + str(stop), from_string=True)
        snps_in_region = input_seq_snps.intersect(target_region)
        for snp in snps_in_region:
            snp_start = int(snp[1])
            snp_stop = int(snp[2])
            snp_id = snp[3]
            ref_ncbi = snp[4]
            observed = snp[5]
            snp_class = snp[6]
            av_het = float(snp[7])
            av_het_se = float(snp[8])
            loc_type = snp[9]
            snp_object = Snp(chromosome_number, snp_start, snp_stop, snp_id, ref_ncbi, observed, snp_class, av_het,
                             av_het_se, loc_type)
            snps_in_range.append(snp_object)
        self.snps = snps_in_range

    def mask_sequence(self, av_het):
        """
        Generates a masked version of the sequence. For each SNP location found within the sequence, the
        nucleotide at that position is changed to an "N"
        """
        # checks to see if the input sequence is on the - strand, and if so converts to the reverse complement
        strand = self.input_sequence.strand
        seq = self.sequence
        # converts the sequence to a list of characters so the locations of the SNPs can be masked with "N"
        seq_list = list(seq)
        # for each SNP in the region calculates the positional offset from the position of the SNP and
        # the start position of the sequence genomic coordinates
        for snp in self.snps:
            if av_het <= snp.av_het:
                offset = snp.coord_start - self.seq_start
                # changes the nucleotide at the position of the SNP to an N in the sequence list
                seq_list[offset] = 'N'
        # converts the sequence list back to a string
        seq = ''.join(seq_list)
        # a string interpretation of the masked sequence is assigned to the maskedSequence instance variable
        self.masked_sequence = str(seq)

    def set_primers(self, min_product_size, max_product_size, primer_opt_size, primer_min_size, primer_max_size,
                    primer_opt_tm, primer_min_tm, primer_max_tm, primer_min_gc, primer_max_gc):
        """
        Generates and sets primers for the maskedSequence using Primer3.
        Primers objects are created for each primer and the list of primers is
        assigned to the primers instance variable for inputSequence.

        Currently the Primer3 parameters are fixed.
        """
        # SOP says to ensure primers are positioned at least 30 bases either side of region of interest
        target_start = self.overhang - 30
        target_end = len(self.masked_sequence) - self.overhang + 30
        target_length = target_end - target_start
        results = primer3.bindings.designPrimers(
            {
                'SEQUENCE_ID': self.target_id,
                'SEQUENCE_TEMPLATE': self.masked_sequence,
                'SEQUENCE_TARGET': [target_start, target_length],
            },
            {
                'PRIMER_PRODUCT_SIZE_RANGE': [min_product_size, max_product_size],
                'PRIMER_OPT_SIZE': primer_opt_size,
                'PRIMER_PICK_LEFT_PRIMER': 1,
                'PRIMER_PICK_INTERNAL_OLIGO': 1,
                'PRIMER_PICK_RIGHT_PRIMER': 1,
                'PRIMER_INTERNAL_MAX_SELF_END': 8,
                'PRIMER_MIN_SIZE': primer_min_size,
                'PRIMER_MAX_SIZE': primer_max_size,
                'PRIMER_INTERNAL_MAX_SIZE': primer_max_size,
                'PRIMER_OPT_TM': primer_opt_tm,
                'PRIMER_MIN_TM': primer_min_tm,
                'PRIMER_MAX_TM': primer_max_tm,
                'PRIMER_MIN_GC': primer_min_gc,
                'PRIMER_MAX_GC': primer_max_gc,
                'PRIMER_THERMODYNAMIC_OLIGO_ALIGNMENT': 1,
                'PRIMER_THERMODYNAMIC_TEMPLATE_ALIGNMENT': 0,
                'PRIMER_LIBERAL_BASE': 1,
                'PRIMER_LIB_AMBIGUITY_CODES_CONSENSUS': 0,
                'PRIMER_LOWERCASE_MASKING': 0,
                'PRIMER_PICK_ANYWAY': 1,
                'PRIMER_EXPLAIN_FLAG': 1,
                'PRIMER_TASK': 'generic',
                'PRIMER_MIN_QUALITY': 0,
                'PRIMER_MIN_END_QUALITY': 0,
                'PRIMER_QUALITY_RANGE_MIN': 0,
                'PRIMER_QUALITY_RANGE_MAX': 100,
                'PRIMER_PAIR_MAX_DIFF_TM': 5.0,
                'PRIMER_TM_FORMULA': 1,
                'PRIMER_PRODUCT_MIN_TM': -1000000.0,
                'PRIMER_PRODUCT_OPT_TM': 0.0,
                'PRIMER_PRODUCT_MAX_TM': 1000000.0,
                'PRIMER_OPT_GC_PERCENT': 50.0,
                'PRIMER_NUM_RETURN': 5,
                'PRIMER_MAX_END_STABILITY': 9.0,
                'PRIMER_MAX_LIBRARY_MISPRIMING': 12.00,
                'PRIMER_PAIR_MAX_LIBRARY_MISPRIMING': 20.00,
                'PRIMER_MAX_TEMPLATE_MISPRIMING_TH': 40.00,
                'PRIMER_PAIR_MAX_TEMPLATE_MISPRIMING_TH': 70.00,
                'PRIMER_MAX_SELF_ANY_TH': 45.0,
                'PRIMER_MAX_SELF_END_TH': 35.0,
                'PRIMER_PAIR_MAX_COMPL_ANY_TH': 45.0,
                'PRIMER_PAIR_MAX_COMPL_END_TH': 35.0,
                'PRIMER_MAX_HAIRPIN_TH': 24.0,
                'PRIMER_MAX_TEMPLATE_MISPRIMING': 12.00,
                'PRIMER_PAIR_MAX_TEMPLATE_MISPRIMING': 24.00,
                'PRIMER_MAX_SELF_ANY': 8.00,
                'PRIMER_MAX_SELF_END': 3.00,
                'PRIMER_PAIR_MAX_COMPL_ANY': 8.00,
                'PRIMER_PAIR_MAX_COMPL_END': 3.00,
                'PRIMER_MAX_NS_ACCEPTED': 0,
                'PRIMER_MAX_POLY_X': 4,
                'PRIMER_INSIDE_PENALTY': -1.0,
                'PRIMER_OUTSIDE_PENALTY': 0,
                'PRIMER_GC_CLAMP': 0,
                'PRIMER_MAX_END_GC': 5,
                'PRIMER_MIN_LEFT_THREE_PRIME_DISTANCE': 3,
                'PRIMER_MIN_RIGHT_THREE_PRIME_DISTANCE': 3,
                'PRIMER_MIN_5_PRIME_OVERLAP_OF_JUNCTION': 7,
                'PRIMER_MIN_3_PRIME_OVERLAP_OF_JUNCTION': 4,
                'PRIMER_SALT_MONOVALENT': 50.0,
                'PRIMER_SALT_CORRECTIONS': 1,
                'PRIMER_SALT_DIVALENT': 1.5,
                'PRIMER_DNTP_CONC': 0.6,
                'PRIMER_DNA_CONC': 50.0,
                'PRIMER_SEQUENCING_SPACING': 500,
                'PRIMER_SEQUENCING_INTERVAL': 250,
                'PRIMER_SEQUENCING_LEAD': 50,
                'PRIMER_SEQUENCING_ACCURACY': 20,
                'PRIMER_WT_SIZE_LT': 1.0,
                'PRIMER_WT_SIZE_GT': 1.0,
                'PRIMER_WT_TM_LT': 1.0,
                'PRIMER_WT_TM_GT': 1.0,
                'PRIMER_WT_GC_PERCENT_LT': 0.0,
                'PRIMER_WT_GC_PERCENT_GT': 0.0,
                'PRIMER_WT_SELF_ANY_TH': 0.0,
                'PRIMER_WT_SELF_END_TH': 0.0,
                'PRIMER_WT_HAIRPIN_TH': 0.0,
                'PRIMER_WT_TEMPLATE_MISPRIMING_TH': 0.0,
                'PRIMER_WT_SELF_ANY': 0.0,
                'PRIMER_WT_SELF_END': 0.0,
                'PRIMER_WT_TEMPLATE_MISPRIMING': 0.0,
                'PRIMER_WT_NUM_NS': 0.0,
                'PRIMER_WT_LIBRARY_MISPRIMING': 0.0,
                'PRIMER_WT_SEQ_QUAL': 0.0,
                'PRIMER_WT_END_QUAL': 0.0,
                'PRIMER_WT_POS_PENALTY': 0.0,
                'PRIMER_WT_END_STABILITY': 0.0,
                'PRIMER_PAIR_WT_PRODUCT_SIZE_LT': 0.0,
                'PRIMER_PAIR_WT_PRODUCT_SIZE_GT': 0.0,
                'PRIMER_PAIR_WT_PRODUCT_TM_LT': 0.0,
                'PRIMER_PAIR_WT_PRODUCT_TM_GT': 0.0,
                'PRIMER_PAIR_WT_COMPL_ANY_TH': 0.0,
                'PRIMER_PAIR_WT_COMPL_END_TH': 0.0,
                'PRIMER_PAIR_WT_TEMPLATE_MISPRIMING_TH': 0.0,
                'PRIMER_PAIR_WT_COMPL_ANY': 0.0,
                'PRIMER_PAIR_WT_COMPL_END': 0.0,
                'PRIMER_PAIR_WT_TEMPLATE_MISPRIMING': 0.0,
                'PRIMER_PAIR_WT_DIFF_TM': 0.0,
                'PRIMER_PAIR_WT_LIBRARY_MISPRIMING': 0.0,
                'PRIMER_PAIR_WT_PR_PENALTY': 1.0,
                'PRIMER_PAIR_WT_IO_PENALTY': 0.0,
                'PRIMER_INTERNAL_MIN_SIZE': 18,
                'PRIMER_INTERNAL_OPT_SIZE': 20,
                'PRIMER_INTERNAL_MIN_TM': 57.0,
                'PRIMER_INTERNAL_OPT_TM': 60.0,
                'PRIMER_INTERNAL_MAX_TM': 63.0,
                'PRIMER_INTERNAL_MIN_GC': 20.0,
                'PRIMER_INTERNAL_OPT_GC_PERCENT': 50.0,
                'PRIMER_INTERNAL_MAX_GC': 80.0,
                'PRIMER_INTERNAL_MAX_SELF_ANY_TH': 47.00,
                'PRIMER_INTERNAL_MAX_SELF_END_TH': 47.00,
                'PRIMER_INTERNAL_MAX_HAIRPIN_TH': 47.00,
                'PRIMER_INTERNAL_MAX_SELF_ANY': 12.00,
                'PRIMER_INTERNAL_MIN_QUALITY': 0,
                'PRIMER_INTERNAL_MAX_NS_ACCEPTED': 0,
                'PRIMER_INTERNAL_MAX_POLY_X': 5,
                'PRIMER_INTERNAL_MAX_LIBRARY_MISHYB': 12.00,
                'PRIMER_INTERNAL_SALT_MONOVALENT': 50.0,
                'PRIMER_INTERNAL_DNA_CONC': 50.0,
                'PRIMER_INTERNAL_SALT_DIVALENT': 1.5,
                'PRIMER_INTERNAL_DNTP_CONC': 0.0,
                'PRIMER_INTERNAL_WT_SIZE_LT': 1.0,
                'PRIMER_INTERNAL_WT_SIZE_GT': 1.0,
                'PRIMER_INTERNAL_WT_TM_LT': 1.0,
                'PRIMER_INTERNAL_WT_TM_GT': 1.0,
                'PRIMER_INTERNAL_WT_GC_PERCENT_LT': 0.0,
                'PRIMER_INTERNAL_WT_GC_PERCENT_GT': 0.0,
                'PRIMER_INTERNAL_WT_SELF_ANY_TH': 0.0,
                'PRIMER_INTERNAL_WT_SELF_END_TH': 0.0,
                'PRIMER_INTERNAL_WT_HAIRPIN_TH': 0.0,
                'PRIMER_INTERNAL_WT_SELF_ANY': 0.0,
                'PRIMER_INTERNAL_WT_SELF_END': 0.0,
                'PRIMER_INTERNAL_WT_NUM_NS': 0.0,
                'PRIMER_INTERNAL_WT_LIBRARY_MISHYB': 0.0,
                'PRIMER_INTERNAL_WT_SEQ_QUAL': 0.0,
                'PRIMER_INTERNAL_WT_END_QUAL': 0.0,
            })
        num_pair_primers = results.get('PRIMER_PAIR_NUM_RETURNED')
        # creates a list containing the required number of primer objects
        primers = [Primer() for _ in range(num_pair_primers)]
        count = 0
        # The output of Primer3 is parsed to extract the primer information which is assigned to the
        # Primer object instance variables
        for primer in primers:
            primer.product_size = results.get(
                'PRIMER_PAIR_' + str(count) + '_PRODUCT_SIZE')
            primer.forward_seq = results.get(
                'PRIMER_LEFT_' + str(count) + '_SEQUENCE')
            primer.forward_start = results.get('PRIMER_LEFT_' + str(count))[0]
            primer.forward_length = results.get('PRIMER_LEFT_' + str(count))[1]
            primer.forward_tm = results.get(
                'PRIMER_LEFT_' + str(count) + '_TM')
            primer.forward_gc = results.get(
                'PRIMER_LEFT_' + str(count) + '_GC_PERCENT')
            primer.reverse_seq = results.get(
                'PRIMER_RIGHT_' + str(count) + '_SEQUENCE')
            primer.reverse_start = results.get('PRIMER_RIGHT_' + str(count))[0]
            primer.reverse_length = results.get(
                'PRIMER_RIGHT_' + str(count))[1]
            primer.reverse_tm = results.get(
                'PRIMER_RIGHT_' + str(count) + '_TM')
            primer.reverse_gc = results.get(
                'PRIMER_RIGHT_' + str(count) + '_GC_PERCENT')
            primer.internal_seq = results.get(
                'PRIMER_INTERNAL_' + str(count) + '_SEQUENCE')
            primer.internal_start = results.get(
                'PRIMER_INTERNAL_' + str(count))[0]
            primer.internal_length = results.get(
                'PRIMER_INTERNAL_' + str(count))[1]
            primer.internal_tm = results.get(
                'PRIMER_INTERNAL_' + str(count) + '_TM')
            primer.internal_gc = results.get(
                'PRIMER_INTERNAL_' + str(count) + '_GC_PERCENT')
            if self.input_sequence.strand == "+":
                primer.forward_genomic_coords = (self.seq_start + primer.forward_start,
                                                 self.seq_start + primer.forward_start + primer.forward_length - 1)
                primer.reverse_genomic_coords = (self.seq_start + primer.reverse_start - primer.reverse_length + 1,
                                                 self.seq_start + primer.reverse_start)
                primer.internal_genomic_coords = (self.seq_start + primer.internal_start,
                                                  self.seq_start + primer.internal_start + primer.internal_length - 1)
            elif self.input_sequence.strand == "-":
                primer.forward_genomic_coords = (self.seq_start - primer.forward_start - primer.forward_length + 1,
                                                 self.seq_start - primer.forward_start)
                primer.reverse_genomic_coords = (self.seq_start - primer.reverse_start,
                                                 self.seq_start - primer.reverse_start + primer.reverse_length - 1)
                primer.internal_genomic_coords = (self.seq_start - primer.internal_start,
                                                  self.seq_start - primer.internal_start - primer.internal_length + 1)
            count += 1
        self.primers = primers


class Primer:
    """
    Primer class for holding information relating to a set of primers (i.e. forward, reverse and internal)
    """

    def __init__(self):
        self.product_size = 0
        self.forward_seq = ""
        self.forward_start = 0
        self.forward_length = 0
        self.forward_tm = 0.0
        self.forward_gc = 0.0
        self.forward_genomic_coords = None
        self.forward_snps = []
        self.reverse_seq = ""
        self.reverse_start = 0
        self.reverse_length = 0
        self.reverse_tm = 0.0
        self.reverse_gc = 0.0
        self.reverse_genomic_coords = None
        self.reverse_snps = []
        self.internal_seq = ""
        self.internal_start = 0
        self.internal_length = 0
        self.internal_tm = 0.0
        self.internal_gc = 0.0
        self.internal_genomic_coords = None
        self.internal_snps = []

    def set_snps(self, target_region):
        """
        Sets the SNPs that are found within the region of the primers
        """
        self.forward_snps = self.find_snps(
            self.forward_genomic_coords, target_region)
        self.reverse_snps = self.find_snps(
            self.reverse_genomic_coords, target_region)
        self.internal_snps = self.find_snps(
            self.internal_genomic_coords, target_region)

    @staticmethod
    def find_snps(genomic_coords, target_region):
        """
        Helper method to find SNPs location within the region of the primer
        """
        target_region_snps = target_region.snps
        primer_site_snps = []
        for snp in target_region_snps:
            if (genomic_coords[0] <= snp.coord_start < genomic_coords[1]) or (
                    genomic_coords[0] < snp.coord_end <= genomic_coords[1]):
                primer_site_snps.append(snp)
        return primer_site_snps


class Snp:
    """
    Snp class holds information about individial SNPs.
    """

    def __init__(self, chrom_number, snp_start, snp_stop, snp_id, ref_ncbi, observed, snp_class, av_het, av_het_se,
                 loc_type):
        self.chrom_number = chrom_number
        self.coord_start = snp_start
        self.coord_end = snp_stop
        self.snp_id = snp_id
        self.ref_NCBI = ref_ncbi
        self.observed = observed
        self.snp_class = snp_class
        self.av_het = av_het
        self.av_het_se = av_het_se
        self.loc_type = loc_type
