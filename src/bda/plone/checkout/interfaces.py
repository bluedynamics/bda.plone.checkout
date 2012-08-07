from zope.interface import Interface


class ICheckoutExtensionLayer(Interface):
    """Browser layer for bda.plone.checkout
    """


class ICheckoutDataAdapter(Interface):
    """Called for persisting checkout.
    """
    
    def save(self, widget, data):
        """Save checkout specific data.
        """