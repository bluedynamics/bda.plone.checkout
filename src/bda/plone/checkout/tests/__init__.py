from zope.interface import alsoProvides
from plone.app.testing import (
    IntegrationTesting,
    PLONE_FIXTURE,
    PloneSandboxLayer,
)
from bda.plone.checkout.interfaces import ICheckoutExtensionLayer


def set_browserlayer(request):
    """Set the BrowserLayer for the request.

    We have to set the browserlayer manually, since importing the profile alone
    doesn't do it in tests.
    """
    alsoProvides(request, ICheckoutExtensionLayer)


class CheckoutLayer(PloneSandboxLayer):
    defaultBases = (PLONE_FIXTURE,)

    def setUpZope(self, app, configurationContext):
        import bda.plone.checkout
        self.loadZCML(package=bda.plone.checkout,
                      context=configurationContext)

    def setUpPloneSite(self, portal):
        self.applyProfile(portal, 'bda.plone.checkout:default')

    def tearDownZope(self, app):
        pass


Checkout_FIXTURE = CartLayer()
Checkout_INTEGRATION_TESTING = IntegrationTesting(
    bases=(Checkout_FIXTURE,),
    name="Checkout:Integration")
