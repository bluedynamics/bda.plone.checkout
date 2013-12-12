import logging
from zope.interface import (
    Interface,
    implementer,
)
from zope.component import adapter
from zope.publisher.interfaces.browser import IBrowserRequest
from node.utils import (
    instance_property,
    UNSET,
)
from bda.plone.cart import deletecookie
from .interfaces import (
    CheckoutError,
    ICheckoutFormPresets,
    ICheckoutAdapter,
    ICheckoutEvent,
    ICheckoutDone,
)


logger = logging.getLogger('bda.plone.checkout')


@implementer(ICheckoutEvent)
class CheckoutEvent(object):

    def __init__(self, context, request, uid):
        self.context = context
        self.request = request
        self.uid = uid


@implementer(ICheckoutDone)
class CheckoutDone(CheckoutEvent): pass


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
                name = '%s.%s' % (provider.fields_name, key)
                vessel[name] = fields[key].extracted
        return 'fake_uid'

    def clear_session(self):
        deletecookie(self.request)

    @property
    def vessel(self):
        """``zope.interface.mapping.IWriteMapping`` providing instance.

        Form data gets written to this object.
        """
        raise NotImplementedError(u"Abstract CheckoutAdapter does not "
                                  u"implement ``vessel``.")

    @property
    def skip_payment(self):
        raise NotImplementedError(u"Abstract CheckoutAdapter does not "
                                  u"implement ``skip_payment``.")

    @property
    def skip_payment_redirect_url(self):
        raise NotImplementedError(u"Abstract CheckoutAdapter does not "
                                  u"implement ``skip_payment_redirect_url``.")


@implementer(ICheckoutFormPresets)
@adapter(Interface, IBrowserRequest)
class NullCheckoutFormPresets(object):
    """Dummy adapter.
    """

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def get_value(field_name):
        """Always return UNSET.
        """
        return UNSET


class NullCheckoutAdapter(CheckoutAdapter):
    """Dummy adapter. provides non persisting write mapping.
    """

    @instance_property
    def vessel(self):
        return dict()
