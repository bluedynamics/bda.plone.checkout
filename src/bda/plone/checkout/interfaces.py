from zope.interface import Interface


class ICheckoutExtensionLayer(Interface):
    """Browser layer for bda.plone.checkout
    """


class IFieldsHandler(Interface):
    """Fields provider persistence adapter.
    """
    
    def save(widget, data):
        """Save fields specific data.
        """