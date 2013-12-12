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


class ICheckoutFormPresets(Interface):
    """Adapter used in checkout process to obtain preset values for checkout
    form fields.

    Possible implementations might aquire information from user property sheets
    or cookies.
    """

    def get_value(field_name):
        """Return value for field name or ``node.utils.UNSET`` if no preset
        value or field name unknown.
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

    skip_payment = Attribute(u"Flag whether to skip payment.")

    skip_payment_redirect_url = Attribute(u"URL to redirect if payment should"
                                          u" be skipped.")

    def save(providers, widget, data):
        """Save fields specific data.

        @param widget: yafowil.base.Widget instance
        @param data: yafowil.base.RuntimeData instance
        @return UUID: unique identifier for stored data
        """

    def clear_session():
        """Clear current shopping session.
        """


class ICheckoutEvent(Interface):
    """Checkout related event.
    """
    context = Attribute(u"Context in which this event was triggered.")

    request = Attribute(u"Current request.")

    uid = Attribute(u"UUID returned by ICheckoutAdapter.save().")


class ICheckoutDone(ICheckoutEvent):
    """This event gets triggered when checkout has been finished.
    """
