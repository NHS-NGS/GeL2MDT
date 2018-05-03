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
from django.test import TestCase, Client
from ..models import *
from django.urls import reverse
from ..factories import *
import factory

# TODO Test validation list, pullt3, variantAdder,
class ViewTests(TestCase):
    """
    Testing the views
    """

    @classmethod
    def setUpTestData(cls):
        user = User.objects.create_user(
            username='test', email='test@gmail.com',
            password='defaultpassword')
        user.is_active = True
        user.save()
        clinician_user = User.objects.create_user(
            username='test2', email='test2@gmail.com',
            password='defaultpassword')
        user.is_active = True
        user.save()

    def test_registration(self):
        response = self.client.post(reverse('register'), {'first_name': 'test',
                                                          'last_name': 'test2',
                                                          'email': 'test@gmail.com',
                                                          'password': 'password',
                                                          'role': 'Clinician',
                                                          'hospital': 'GOSH'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Thank you for registering', response.content.decode())

    def setUp(self):
        self.client = Client()
        self.sample_type = 'raredisease'
        self.clinician = ClinicianFactory(email='test2@gmail.com')
        self.client.login(username='test', password='defaultpassword')
        self.family = FamilyFactory()
        self.proband = ProbandFactory(family=self.family)
        self.ir_family = InterpretationReportFamilyFactory(participant_family=self.family)
        self.gel_ir = GELInterpretationReportFactory(ir_family=self.ir_family)
        self.ir_panels = InterpretationReportFamilyPanelFactory(ir_family=self.ir_family)
        self.gene = GeneFactory(hgnc_name='KJHAKDS')
        self.transcript1 = TranscriptFactory(gene=self.gene)
        self.transcript2 = TranscriptFactory(gene=self.gene)
        self.variant = VariantFactory()
        self.proband_variant = ProbandVariantFactory(interpretation_report=self.gel_ir,
                                                     variant=self.variant)
        self.rdr = self.proband_variant.create_rare_disease_report()
        self.ptv = ProbandTranscriptVariantFactory(proband_variant=self.proband_variant,
                                                   transcript=self.transcript1,
                                                   selected=True)
        self.ptv = ProbandTranscriptVariantFactory(proband_variant=self.proband_variant,
                                                   transcript=self.transcript2,
                                                   selected=False)
        self.tv1 = TranscriptVariantFactory(transcript=self.transcript1,
                                           variant=self.variant)
        self.tv2 = TranscriptVariantFactory(transcript=self.transcript2,
                                           variant=self.variant)
        self.reportevent = ReportEventFactory(proband_variant=self.proband_variant,
                                              panel=self.ir_panels.panel)
        self.mdt = MDTFactory()

    def test_index_view(self):
        """
        Tests whether the index page can be accessed
        """
        response = self.client.get(reverse('index'))
        self.assertEquals(response.status_code, 200)

    def test_clin_index_view(self):
        self.client.login(username='test2', password='defaultpassword')
        response = self.client.get(reverse('index'), follow=True)
        self.assertRedirects(response, '/clinician/', status_code=302,
                             target_status_code=200, fetch_redirect_response=True)

    def test_rare_disease_main(self):
        """
        Tests whether the rare disease page can be accessed
        """
        response = self.client.get(reverse('rare-disease-main'),
                                   content_type='application/json',
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)

    def test_clin_rare_disease_main(self):
        """
        Tests whether the rare disease page can be accessed when user is clinician
        """
        self.client.login(username='test2', password='defaultpassword')
        response = self.client.get(reverse('rare-disease-main'),
                                   follow=True)
        self.assertRedirects(response, '/clinician/rare-disease-main', status_code=302,
                             target_status_code=200, fetch_redirect_response=True)

    def test_cancer_main(self):
        """
        Tests whether the cancer page can be accessed
        """
        response = self.client.get(reverse('cancer-main'),
                                   content_type='application/json',
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEquals(response.status_code, 200)

    def test_clin_cancer_main(self):
        """
        Tests whether the cancer page can be accessed when user is clinician
        """
        self.client.login(username='test2', password='defaultpassword')
        response = self.client.get(reverse('cancer-main'),
                                   follow=True)
        self.assertRedirects(response, '/clinician/cancer-main', status_code=302,
                             target_status_code=200, fetch_redirect_response=True)

    def test_gelir_api(self):
        """
        Test that access to GELIR API is available
        """
        response = self.client.get(reverse('gelir-json', args=[self.sample_type]))
        self.assertContains(response, self.proband.gel_id)
        self.assertEquals(response.status_code, 200)

    def test_proband_view(self):
        """
        Tests the sample page for the factory case and you can see the patient
        and variant details
        """
        response = self.client.get(reverse('proband-view', args=[self.gel_ir.id]))
        self.assertContains(response, self.proband.gel_id)
        self.assertContains(response, self.proband.surname)
        self.assertContains(response, self.gene)
        self.assertContains(response, self.transcript1.name) # Should contain selected transcript
        self.assertEquals(response.status_code, 200)

    def test_variant_view(self):
        """
        Tests whether the variant page can be accessed
        """
        response = self.client.get(reverse('variant-view', args=[self.variant.id]))
        self.assertContains(response, self.variant.chromosome)
        self.assertContains(response, self.variant.db_snp_id)
        self.assertContains(response, self.proband.gel_id)
        self.assertContains(response, self.variant.reference)
        self.assertEquals(response.status_code, 200)

    def test_update_sample(self):
        """
        Checks whether samples info can be updated
        """
        response = self.client.post(reverse('update-proband', args=[self.gel_ir.id]),
                                    {'outcome': 'testoutcome',
                                    'comment': 'testcomment',
                                     'case_status': 'N',
                                     'pilot_case': True,
                                     'mdt_status': 'R',
                                     'case_sent': False,
                                     'no_primary_findings': False},
                                     follow=True)
        self.assertContains(response, 'Proband Updated')
        self.assertEquals(response.status_code, 200)
        proband = Proband.objects.get(id=self.proband.id)
        gelir = GELInterpretationReport.objects.get(id=self.gel_ir.id)
        self.assertEqual(proband.comment, 'testcomment')
        self.assertEqual(gelir.pilot_case, True)

    def test_select_transcript(self):
        """
        View for selecting transcript for variant
        """
        response = self.client.post(reverse('select-transcript', args=[self.gel_ir.id,
                                                                       self.proband_variant.id]))
        self.assertContains(response, self.transcript1.name)
        self.assertContains(response, self.transcript2.name)
        self.assertEquals(response.status_code, 200)

    def test_update_transcript(self):
        """
        Update transcript for variant
        """
        response = self.client.post(reverse('update-transcript',
                                            args=[self.gel_ir.id,
                                                  self.proband_variant.id,
                                                  self.transcript2.id]),
                                    follow=True)
        self.assertContains(response, 'Transcript Updated')
        self.assertEquals(response.status_code, 200)
        response = self.client.get(reverse('proband-view', args=[self.gel_ir.id]))
        self.assertContains(response, self.transcript2.name)

    def test_start_mdt(self):
        """
        View for starting mdt
        """
        response = self.client.get(reverse('start-mdt', args=[self.sample_type]), follow=True)
        self.assertContains(response, self.proband.gel_id)
        self.assertEqual(response.status_code, 200)

    def test_edit_mdt(self):
        """
        Allows you to edit samples in MDT
        """
        response = self.client.get(reverse('edit-mdt', args=[self.sample_type, self.mdt.id]))
        self.assertContains(response, self.proband.gel_id)
        self.assertEqual(response.status_code, 200)

    def test_add_ir_to_mdt(self):
        """
        Adding case to MDT
        """
        response = self.client.post(reverse('add-ir-to-mdt',
                                            args=[self.mdt.id, self.gel_ir.id]),
                                    follow=True)
        self.assertContains(response, 'Remove')
        self.assertEquals(response.status_code, 200)
        assert self.gel_ir.id in MDTReport.objects.filter(MDT=self.mdt).values_list('interpretation_report', flat=True)


    def test_remove_ir_from_mdt(self):
        """
        Removing case to MDT
        """
        response = self.client.post(reverse('add-ir-to-mdt',
                                            args=[self.mdt.id, self.gel_ir.id]),
                                    follow=True)
        response = self.client.post(reverse('remove-ir-from-mdt',
                                            args=[self.mdt.id, self.gel_ir.id]),
                                    follow=True)
        self.assertContains(response, 'Add')
        self.assertContains(response, 'Select samples for MDT')
        self.assertEquals(response.status_code, 200)

    def test_mdt_view(self):
        """
        Main MDT view and you can update MDTForm
        """
        self.client.post(reverse('add-ir-to-mdt',
                                            args=[self.mdt.id, self.gel_ir.id]),
                                    follow=True)
        response = self.client.get(reverse('mdt-view',
                                           args=[self.mdt.id]))
        self.assertContains(response, self.proband.gel_id)
        self.assertEquals(response.status_code, 200)
        response = self.client.post(reverse('mdt-view', args=[self.mdt.id]),
                                    {'status':'C',
                                     'date_of_mdt': datetime.datetime.now()}, follow=True)
        self.assertContains(response, 'Completed')
        self.assertContains(response, 'MDT Updated')
        self.assertEquals(response.status_code, 200)

    def test_mdt_proband_view(self):
        """
        See MDT proband view
        """
        session = self.client.session
        session['mdt_id'] = self.mdt.id
        session.save()
        self.client.post(reverse('add-ir-to-mdt',
                                 args=[self.mdt.id, self.gel_ir.id]),
                         follow=True)
        response = self.client.get(reverse('mdt-proband-view', args=[self.mdt.id,
                                                                     self.gel_ir.id, 1]))
        self.assertContains(response, self.proband.forename)
        self.assertContains(response, self.transcript2.gene)
        self.assertEquals(response.status_code, 200)

    def test_edit_mdt_proband(self):
        """
        Editing MDT proband discussion and actions
        """
        session = self.client.session
        session['mdt_id'] = self.mdt.id
        session.save()
        response = self.client.post(reverse('edit-mdt-proband', args=[self.gel_ir.id]),
                                    {'discussion': 'asdjkasjkdjska',
                                     'action': 'dakflajdfkl'})
        self.assertContains(response, 'dakflajdfkl')
        self.assertEquals(response.status_code, 200)

    def test_recent_mdts(self):
        """
        You can see recent mdt's
        """
        response = self.client.get(reverse('recent-mdt', args=[self.sample_type]))
        self.assertEquals(response.status_code, 200)

    def test_select_attendees_for_mdt(self):
        """
        Can select and show existing attendees
        """
        response = self.client.get(reverse('select-attendees-for-mdt', args=[self.mdt.id]))
        self.assertContains(response, self.family.clinician.name)
        self.assertEquals(response.status_code, 200)

    def test_add_attendee_to_mdt(self):
        """
        Can add a attendee to a MDT
        """
        response = self.client.post(reverse('add-attendee-to-mdt', args=[self.mdt.id,
                                                                          self.family.clinician.id,
                                                                          'Clinician']),
                                    follow=True)
        self.assertContains(response, self.family.clinician.name)
        self.assertIn(self.family.clinician, self.mdt.clinicians.all())
        self.assertEquals(response.status_code, 200)

    def test_add_new_attendee(self):
        """
        Can add a new attendee
        """
        session = self.client.session
        session['mdt_id'] = self.mdt.id
        session.save()
        response = self.client.post(reverse('add-new-attendee'),
                                    {'name': 'Paddy',
                                     'hospital':'GOSH',
                                     'email': 'gosh@gosh.nhs.uk',
                                     'role': 'Clinician'}, follow=True)
        self.assertContains(response, 'Attendee Added')
        self.assertEquals(response.status_code, 200)

    def test_export_mdt(self):
        """
        Testing the mdt exporting function
        """
        self.client.post(reverse('add-ir-to-mdt',
                                 args=[self.mdt.id, self.gel_ir.id]),
                         follow=True)
        response = self.client.post(reverse('export-mdt', args=[self.mdt.id]), follow=True)
        self.assertContains(response, self.ir_family.ir_family_id)
        self.assertContains(response, self.proband.surname)
        self.assertContains(response, self.transcript1.gene)
        self.assertEquals(response.status_code, 200)

    def test_export_mdt_outcome_form(self):
        """
        Testing the mdm outcome exporting function
        """
        self.client.post(reverse('add-ir-to-mdt',
                                            args=[self.mdt.id, self.gel_ir.id]),
                                    follow=True)
        response = self.client.post(reverse('export-mdt-outcome', args=[self.gel_ir.id]))
        self.assertIn(self.ir_family.ir_family_id, response['Content-Disposition'])  # No idea how to test content of this
        self.assertEquals(response.status_code, 200)

    def test_delete_mdt(self):
        """
        #Delete MDT
        """
        response = self.client.post(reverse('delete-mdt', args=[self.mdt.id]), follow=True)
        self.assertContains(response, 'MDT Deleted')
        self.assertEquals(response.status_code, 200)

    def test_negative_report(self):
        """
        Test negative report
        """
        response = self.client.post(reverse('negative_report', args=[self.gel_ir.id]))
        self.assertContains(response, 'Whole genome sequencing')
        self.assertContains(response, self.proband.nhs_number)

    def gel_report(self):
        """
        Test this crap GEL view
        """
        response = self.client.get(reverse('genomics-england'), follow=True)  # Start MDT
        self.assertContains(response, 'Clinical Report Version:')
        self.assertContains(response, 'Panel Version:')
        self.assertEquals(response.status_code, 200)

    def test_validation_list(self):
        """
        Test you can see the variants which require validation
        """
        response = self.client.get(reverse('validation-list', args=[self.sample_type]))
        self.assertContains(response, self.transcript2.gene)
        self.assertEqual(response.status_code, 200)

    def test_variant_for_validation(self):
        '''
        Test you can change the validation status of a variant and it will be found in the validation list
        '''
        response = self.client.post(reverse('variant-for-validation', args=[self.proband_variant.id]), follow=True)
        self.assertContains(response, 'Validation Status Updated')
        self.assertEqual(response.status_code, 200)

    def test_clinician_redirect(self):
        '''
        Tests that when you are a clinician, you get redirected to the correct view
        '''
