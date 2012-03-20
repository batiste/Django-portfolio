"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from market.models import normalize

class SimpleTest(TestCase):

    def test_normalize(self):
        """
        """
        self.assertEqual(normalize(0.5, 10, bigger_better=True, limits=[0, 1]), 0.5)
        self.assertEqual(normalize(0.5, -10, bigger_better=True, limits=[0, 1]), -0.5)
        self.assertEqual(normalize(50, 10, bigger_better=False, limits=[0, 100]), 40)
        self.assertEqual(normalize(50, 10, bigger_better=True, limits=[0, 100]), -40)