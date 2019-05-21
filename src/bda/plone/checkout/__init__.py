from bda.plone.cart import deletecookie
from bda.plone.checkout.interfaces import CheckoutError
from bda.plone.checkout.interfaces import ICheckoutAdapter
from bda.plone.checkout.interfaces import ICheckoutDone
from bda.plone.checkout.interfaces import ICheckoutEvent
from bda.plone.checkout.interfaces import ICheckoutFormPresets
from node.utils import instance_property
from node.utils import UNSET
from zope.component import adapter
from zope.i18nmessageid import MessageFactory
from zope.interface import implementer
from zope.interface import Interface
from zope.publisher.interfaces.browser import IBrowserRequest

import logging


# what is this?
CheckoutError  # API import / pep 8 pleasure.


message_factory = MessageFactory("bda.plone.checkout")
logger = logging.getLogger("bda.plone.checkout")


@implementer(ICheckoutEvent)
class CheckoutEvent(object):
    def __init__(self, context, request, uid):
        self.context = context
        self.request = request
        self.uid = uid


@implementer(ICheckoutDone)
class CheckoutDone(CheckoutEvent):
    pass


@implementer(ICheckoutAdapter)
@adapter(Interface, IBrowserRequest)
class CheckoutAdapter(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def save(self, providers, widget, data):
        vessel = self.vessel
        for provider in providers:
            if provider.ignore_on_save:
                continue
            fields = data.get(provider.fields_name, dict())
            for key in fields:
                name = "%s.%s" % (provider.fields_name, key)
                vessel[name] = fields[key].extracted
        return "fake_uid"

    def clear_session(self):
        deletecookie(self.request)

    @property
    def vessel(self):
        """``zope.interface.mapping.IWriteMapping`` providing instance.

        Form data gets written to this object.
        """
        raise NotImplementedError(
            u"Abstract CheckoutAdapter does not " u"implement ``vessel``."
        )

    @property
    def skip_payment(self):
        raise NotImplementedError(
            u"Abstract CheckoutAdapter does not " u"implement ``skip_payment``."
        )

    @property
    def skip_payment_redirect_url(self):
        raise NotImplementedError(
            u"Abstract CheckoutAdapter does not "
            u"implement ``skip_payment_redirect_url``."
        )


@implementer(ICheckoutFormPresets)
@adapter(Interface, IBrowserRequest)
class NullCheckoutFormPresets(object):
    """Dummy adapter.
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def get_value(self, field_name):
        """Always return UNSET.
        """
        return UNSET


class NullCheckoutAdapter(CheckoutAdapter):
    """Dummy adapter. provides non persisting write mapping.
    """

    @instance_property
    def vessel(self):
        return dict()
