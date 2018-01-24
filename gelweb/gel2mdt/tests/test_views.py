import unittest
from django.test import TestCase
from ..models import *
from django.urls import reverse

class ViewTests(TestCase):
    """
    Testing the views
    """
    def login_test_user(self):
        self.client.login(username='test@gmail.com', password='test')
        return self

    def logout_test_user(self):
        self.client.logout()
        return self

    def setup(self):
        pass

    def test_registration(self):
        response = self.client.post(reverse('register'), {'first_name': 'test',
                                                          'last_name': 'test2',
                                                          'email': 'test@gmail.com',
                                                          'password': 'password',
                                                          'role': 'CS',
                                                          'hospital': 'GOSH'}, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Thank you for registering', response.content.decode())
