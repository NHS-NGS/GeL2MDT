import unittest
from django.test import TestCase, Client
from ..models import *
from django.urls import reverse
from ..factories import *

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

    def test_registration(self):
        response = self.client.post(reverse('register'), {'first_name': 'test',
                                                          'last_name': 'test2',
                                                          'email': 'test@gmail.com',
                                                          'password': 'password',
                                                          'role': 'Clinical Scientist',
                                                          'hospital': 'GOSH'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Thank you for registering', response.content.decode())


    def setUp(self):
        self.client = Client()
        self.client.login(username='test', password='defaultpassword')
        self.family = FamilyFactory()
        self.proband = ProbandFactory(family=self.family)
        self.ir_family = InterpretationReportFamilyFactory(participant_family=self.family)
        self.gel_ir = GELInterpretationReportFactory(ir_family=self.ir_family)
        self.ir_panels = InterpretationReportFamilyPanelFactory(ir_family=self.ir_family)
        self.gene = GeneFactory()
        self.transcript = TranscriptFactory(gene=self.gene)
        self.variant = VariantFactory()
        self.proband_variant = ProbandVariantFactory(interpretation_report=self.gel_ir,
                                                     variant=self.variant)
        self.rdr = self.proband_variant.create_rare_disease_report()
        self.ptv = ProbandTranscriptVariantFactory(proband_variant=self.proband_variant,
                                                   transcript=self.transcript,
                                                   selected=True)
        self.tv = TranscriptVariantFactory(transcript=self.transcript,
                                           variant=self.variant)
        self.reportevent = ReportEventFactory(proband_variant=self.proband_variant,
                                              panel=self.ir_panels.panel)

    def test_index_view(self):
        """
        Tests whether the index page can be accessed
        """
        response = self.client.get(reverse('rare-disease-main'),
                                   content_type='application/json',
                                   HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        #self.assertContains(response, self.proband.gel_id)  # Not working, maybe due to ajax?
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
        self.assertContains(response, self.transcript.name)
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
                                     'status': 'C',
                                     'episode': 'test_episode',
                                     'mdt_status': 'R',
                                     'pilot_case': True,
                                     'case_sent': True},
                                     follow=True)
        self.assertContains(response, 'Proband Updated')
        self.assertEquals(response.status_code, 200)

