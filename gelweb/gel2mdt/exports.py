from .models import *
import csv
from docx import Document
from django.conf import settings
import os
from docx.shared import Pt

def write_mdt_export(writer, mdt_instance, mdt_reports):
    writer.writerow(['CIP_ID', 'Forename', 'Surname', 'DOB', 'Hospital_ID',
                     'Variant/Zygosity', 'Panel'])

    for report in mdt_reports:
        proband_variants = ProbandVariant.objects.filter(interpretation_report=report.interpretation_report)
        panels = InterpretationReportFamilyPanel.objects.filter(ir_family=report.interpretation_report.ir_family)
        pv_output = []
        for proband_variant in proband_variants:
            transcript = proband_variant.get_transcript()
            transcript_variant = proband_variant.get_transcript_variant()
            if transcript and transcript_variant:
                hgvs_c = None
                hgvs_p = None
                hgvs_c_split = transcript_variant.hgvs_c.split(':')
                hgvs_p_split = transcript_variant.hgvs_p.split(':')
                if len(hgvs_c_split) > 1:
                    hgvs_c = hgvs_c_split[1]
                if len(hgvs_p_split) > 1:
                    hgvs_p = hgvs_p_split[1]
                pv_output.append(f'{transcript.gene}, '
                                 f'{hgvs_c}, '
                                 f'{hgvs_p}, '
                                 f'{proband_variant.zygosity}')
        panel_names = []
        for panel in panels:
            panel_names.append(f'{panel.panel.panel.panel_name}_'
                               f'{panel.panel.version_number}')
        writer.writerow([report.interpretation_report.ir_family.ir_family_id,
                         report.interpretation_report.ir_family.participant_family.proband.forename,
                         report.interpretation_report.ir_family.participant_family.proband.surname,
                         report.interpretation_report.ir_family.participant_family.proband.date_of_birth.date(),
                         report.interpretation_report.ir_family.participant_family.proband.local_id,
                         '\n'.join(pv_output),
                         '\n'.join(panel_names)])
    return writer


def write_mdt_outcome_template(report):
    """
    :param pk: Sample Gel Participant ID
    :return: Reads a template and writes it out to the user
    """
    document = Document()
    document.add_picture(os.path.join(settings.STATIC_DIR, 'nhs_image.png'))
    document.add_heading('Genomics MDM record', 0)

    table = document.add_table(rows=2, cols=4, style='Table Grid')
    heading_cells = table.rows[0].cells
    heading_cells[0].paragraphs[0].add_run('Patient Name').bold=True
    heading_cells[1].paragraphs[0].add_run('DOB').bold=True
    heading_cells[2].paragraphs[0].add_run('NHS number').bold=True
    heading_cells[3].paragraphs[0].add_run('Local ID').bold=True

    row = table.rows[1].cells
    row[0].text = str(report.ir_family.participant_family.proband.forename) \
                  + ' ' \
                  + str(report.ir_family.participant_family.proband.surname)
    row[1].text = str(report.ir_family.participant_family.proband.date_of_birth.date())
    row[2].text = report.ir_family.participant_family.proband.nhs_number
    if report.ir_family.participant_family.proband.local_id:
        row[3].text = report.ir_family.participant_family.proband.local_id

    paragraph = document.add_paragraph()
    paragraph.add_run()
    paragraph.add_run('Referring Clinician: ').bold=True
    paragraph.add_run('{}\n'.format(report.ir_family.participant_family.clinician))
    paragraph.add_run('Department/Hospital: ').bold=True
    paragraph.add_run('{}\n'.format(report.ir_family.participant_family.proband.gmc))
    paragraph.add_run('Study: ').bold=True
    paragraph.add_run('100,000 genomes (whole genome sequencing)\n')
    paragraph.add_run('OPA ID: ').bold = True
    paragraph.add_run('{}\n'.format(report.ir_family.ir_family_id))
    paragraph.add_run('Family ID: ').bold=True
    paragraph.add_run('{}\n'.format(report.ir_family.participant_family.gel_family_id))
    paragraph.add_run('Genome Build: ').bold=True
    paragraph.add_run('{}\n\n'.format(report.assembly))

    # paragraph.add_run('Phenotype summary: ').bold=True
    # if sample_info.hpo_terms:
    #    paragraph.add_run('{}\n'.format(', '.join(list(json.loads(sample_info.hpo_terms)))))

    proband_variants = list(ProbandVariant.objects.filter(interpretation_report=report))

    run = paragraph.add_run('MDT:\n')
    run.font.size = Pt(16)
    run.underline = True
    run.bold = True

    if proband_variants:
        run = paragraph.add_run('Variant Outcome Summary:\n')
        run.font.size = Pt(13)
        run.underline = True
        run.bold = True

        table = document.add_table(rows=1, cols=7, style='Table Grid')
        heading_cells = table.rows[0].cells
        run = heading_cells[0].paragraphs[0].add_run('Gene')
        run.bold=True
        run.font.size = Pt(9)
        run = heading_cells[1].paragraphs[0].add_run('HGVSg')
        run.bold = True
        run.font.size = Pt(9)
        run = heading_cells[2].paragraphs[0].add_run('HGVSc')
        run.bold = True
        run.font.size = Pt(9)
        run = heading_cells[3].paragraphs[0].add_run('HGVSp')
        run.bold = True
        run.font.size = Pt(9)
        run = heading_cells[4].paragraphs[0].add_run('Zygosity')
        run.bold = True
        run.font.size = Pt(9)
        run = heading_cells[5].paragraphs[0].add_run('Phenotype Contribution')
        run.bold = True
        run.font.size = Pt(9)
        run = heading_cells[6].paragraphs[0].add_run('Class')
        run.bold = True
        run.font.size = Pt(9)

    for proband_variant in proband_variants:
        cells = table.add_row().cells
        transcript = proband_variant.get_transcript()
        transcript_variant = proband_variant.get_transcript_variant()
        rdr = proband_variant.create_rare_disease_report()
        run = cells[0].paragraphs[0].add_run(str(transcript.gene))
        run.font.size = Pt(7)
        run = cells[1].paragraphs[0].add_run(str(transcript_variant.hgvs_g))
        run.font.size = Pt(7)
        run = cells[2].paragraphs[0].add_run(str(transcript_variant.hgvs_c))
        run.font.size = Pt(7)
        run = cells[3].paragraphs[0].add_run(str(transcript_variant.hgvs_p))
        run.font.size = Pt(7)
        run = cells[4].paragraphs[0].add_run(str(proband_variant.zygosity))
        run.font.size = Pt(7)
        run = cells[5].paragraphs[0].add_run(str(rdr.get_contribution_to_phenotype_display()))
        run.font.size = Pt(7)
        run = cells[6].paragraphs[0].add_run(str(rdr.classification))
        run.font.size = Pt(7)

    mdt_linkage_list = MDTReport.objects.filter(interpretation_report=report).values('MDT')
    mdt = MDT.objects.filter(id__in=mdt_linkage_list).order_by('-date_of_mdt').first()

    paragraph = document.add_paragraph()

    paragraph.add_run('MDT Date: ').bold = True
    paragraph.add_run('{}\n'.format(mdt.date_of_mdt.date()))
    paragraph.add_run('MDT Attendees: ').bold = True
    clinicians = Clinician.objects.filter(mdt=mdt.id).values_list('name', flat=True)
    clinical_scientists = ClinicalScientist.objects.filter(mdt=mdt.id).values_list('name', flat=True)
    other_staff = OtherStaff.objects.filter(mdt=mdt.id).values_list('name', flat=True)

    attendees = list(clinicians) + list(clinical_scientists) + list(other_staff)
    paragraph.add_run('{}\n\n'.format(','.join(attendees)))
    paragraph.add_run()
    run = paragraph.add_run('Discussion:\n')
    run.font.size = Pt(13)
    run.underline = True
    run.bold = True
    paragraph.add_run('{}\n\n'.format(report.ir_family.participant_family.proband.discussion.rstrip()))
    run = paragraph.add_run('Action:\n')
    run.font.size = Pt(13)
    run.underline = True
    run.bold = True
    paragraph.add_run('{}\n'.format(report.ir_family.participant_family.proband.action.rstrip()))
    return document, mdt

