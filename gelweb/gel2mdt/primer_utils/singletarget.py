import csv
import requests
import sys
from pybedtools import BedTool
from . import autoprimer as ap
from ..config import load_config


class Variant:
    def __init__(self, chromosome, start, build, **kwargs):
        self.filename = ""
        self.gene = ""
        self.strand = ""
        self.build = build
        self.chromosome = chromosome
        self.start = start
        self.end = ""
        self.lenght = ""
        self.ref = ""
        self.alt = ""
        self.inheritance = ""
        self.condition = ""
        self.hgvsc = ""
        self.hgvsp = ""
        self.zygosity = ""
        self.pathogenicity = ""
        self.contribution = ""
        self.depth = ""
        self.af_max = ""
        for key, value in kwargs.items():
            setattr(self, key, value)


def get_surrounding_sequence(variant):
    # sets start and stop for surrounding sequence to 500 bases upstream and downstream of variant start position
    start = int(variant.start) - 500
    stop = int(variant.start) + 500
    variant_bed = BedTool(variant.chromosome + " " +
                          str(start) + " " + str(stop), from_string=True)
    # set the genome to use
    config_dict = load_config.LoadConfig().load()
    if '19' in variant.build or '37' in variant.build:
        ucsc_fasta = BedTool(
            config_dict['primer_hg19_genome'])
    elif '38' in variant.build:
        ucsc_fasta = BedTool(
            config_dict['primer_hg38_genome'])
    # use pybedtools API to return the sequence
    genomic_region = variant_bed.sequence(fi=ucsc_fasta, tab=True)
    bedtools_result = open(genomic_region.seqfn).read()
    raw_sequence = bedtools_result.strip().split('\t')[1]
    return raw_sequence.upper()


def look_up_strand(gene_symbol):
    server = "https://rest.ensembl.org"
    ext = "/lookup/symbol/homo_sapiens/" + gene_symbol + "?expand=1"

    r = requests.get(
        server + ext, headers={"Content-Type": "application/json"})

    if not r.ok:
        r.raise_for_status()
        sys.exit()

    decoded = r.json()
    if repr(decoded['strand']) == "1":
        strand = "Forward (+)"
    elif repr(decoded['strand']) == "-1":
        strand = "Reverse (-)"
    return strand


def design_from_coord(variant):
    print('chromosome = ' + variant.chromosome)
    print('coord = ' + variant.start)
    print("build = " + variant.build)
    sequence = get_surrounding_sequence(variant)
    input_sequence = ap.InputSequence(variant.hgvsc, sequence, gene_name=variant.gene, chrom_number=variant.chromosome,
                                      genomic_coords=(int(variant.start) - 500, int(variant.start) + 500), strand="+")
    target = ap.TargetRegion(variant.chromosome + ":" + variant.start, sequence, int(
        variant.start) - 500, int(variant.start) + 500, 450, input_sequence)
    print(type(target))
    input_sequence.set_snps_bed(variant.build)
    input_sequence.target_regions.append(target)

    target_regions = input_sequence.target_regions
    designed_primers = []
    # there will only be 1 target region as only a single target is supplied to the function
    for target in target_regions:
        target.set_snps()
        target.mask_sequence(av_het=0.02) # masks SNPs with av_het > 0.02
        print(target.masked_sequence)
        # set to default settings
        target.set_primers(min_product_size=300, max_product_size=750, primer_opt_size=20, primer_min_size=18,
                           primer_max_size=27, primer_opt_tm=60, primer_min_tm=57, primer_max_tm=63,
                           primer_min_gc=20, primer_max_gc=80)
        primers = target.primers
        for primer in primers:
            primer.set_snps(target)
            print(primer.forward_seq, primer.forward_genomic_coords,
                  primer.reverse_seq, primer.reverse_genomic_coords)
        designed_primers = target.primers
    write_to_csv(input_sequence, variant)
    return designed_primers


def write_to_csv(input_sequence, variant):
    """
    Writes primers that have been designed to a CSV file
    """
    # inputSequence ID used as the filename
    filename = variant.chromosome + '-' + variant.start + '-primers.csv'
    targets = input_sequence.target_regions
    # with open('output/' + filename + '.csv', 'w') as csvfile:
    config_dict = load_config.LoadConfig().load()
    with open(config_dict['primer_output_dir'] + filename, 'w') as csvfile:
        f = csv.writer(csvfile, delimiter=',',
                       quotechar=',', quoting=csv.QUOTE_MINIMAL)
        f.writerow(['Gene', 'Strand', 'Target', 'Product size', 'Forward primer sequence', 'Genomic Coords', 'Forward TM',
                    'Forward GC %', 'Forward SNPs', 'Reverse primer sequence', 'Genomic Coords', 'Reverse TM',
                    'Reverse GC %', 'Reverse SNPs'])
        for target in targets:
            primer_list = target.primers
            # Primer temperatures and GC% rounded to 2 decimal places
            for primer in primer_list:
                forward_snps = ''
                reverse_snps = ''
                for snp in primer.forward_snps:
                    forward_snps = forward_snps + snp.snp_id + \
                        ' (' + str(round(snp.av_het, 4)) + ') '
                for snp in primer.reverse_snps:
                    reverse_snps = reverse_snps + snp.snp_id + \
                        ' (' + str(round(snp.av_het, 4)) + ') '
                f.writerow([input_sequence.gene_name, variant.strand, target.target_id, primer.product_size, primer.forward_seq,
                            input_sequence.chrom_number + ":" + str(primer.forward_genomic_coords[0]) + "-" + str(
                                primer.forward_genomic_coords[1]), round(primer.forward_tm, 2),
                            round(primer.forward_gc,
                                  2), forward_snps, primer.reverse_seq,
                            input_sequence.chrom_number + ":" + str(primer.reverse_genomic_coords[0]) + "-" + str(
                                primer.reverse_genomic_coords[1]),
                            round(primer.reverse_tm, 2), round(primer.reverse_gc, 2), reverse_snps])


def design_primers(chromosome, coordinate, assembly, gene_symbol):
    print(assembly)
    #strand = look_up_strand(gene_symbol)
    variant = Variant(chromosome, coordinate, assembly, gene = gene_symbol)#, strand = strand)
    return design_from_coord(variant)


if __name__ == '__main__':
    # variants = read_in_variants()
    # for variant in variants:
    #     design_from_coord(variant)
    chromosome = sys.argv[1]
    coordinate = sys.argv[2]
    genome_build = sys.argv[3]
    variant = Variant(chromosome, coordinate, genome_build)
    design_from_coord(variant)
