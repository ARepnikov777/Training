import unittest
from discount import total
from shipping import shipping
class Existing(unittest.TestCase):
    def test_no_discount(self): self.assertEqual(total(100, 2), 200)
    def test_paid_shipping(self): self.assertEqual(shipping(4000), 500)
