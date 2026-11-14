import unittest
from cart import total

class ExistingTests(unittest.TestCase):
    def test_without_discount(self):
        self.assertEqual(total(1000, 2, 0), 2000)
