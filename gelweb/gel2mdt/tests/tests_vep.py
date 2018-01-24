import unittest
from django.test import TestCase
from . import run_vep_batch

class VepTestCase(TestCase):
    run_vep_batch.genetate_transcipts()

