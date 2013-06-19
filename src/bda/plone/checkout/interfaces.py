from zope.interface import (
    Interface,
    Attribute,
)


class CheckoutError(Exception):
    """Thrown if ``ICheckoutAdapter.save`` fails.
    """


class ICheckoutExtensionLayer(Interface):
    """Browser layer for bda.plone.checkout.
    """


class IFieldsProvider(Interface):
    """Form fields provider for checkout.
    """
    fields_name = Attribute(u"Name of this fields provider.")

    def extend(form):
        """Extend form with arbitrary fields.
        """


class ICheckoutAdapter(Interface):
    """Checkout persistence adapter.
    """
    vessel = Attribute(u"``zope.interface.mapping.IWriteMapping providing`` "
                       u"instance.")

    def save(providers, widget, data):
        """Save fields specific data.

        @param widget: yafowil.base.Widget instance
        @param data: yafowil.base.RuntimeData instance
        @return UUID: unique identifier for stored data
        """

    def clear_session():
        """Clear current shopping session.
        """
