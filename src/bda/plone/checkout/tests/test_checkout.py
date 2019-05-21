import unittest
from bda.plone.checkout.tests import Checkout_INTEGRATION_TESTING
from bda.plone.checkout.tests import set_browserlayer


class TestCheckout(unittest.TestCase):
    layer = Checkout_INTEGRATION_TESTING

    def setUp(self):
        self.portal = self.layer["portal"]
        self.request = self.layer["request"]
        set_browserlayer(self.request)

    def test_foo(self):
        self.assertEquals(1, 1)
