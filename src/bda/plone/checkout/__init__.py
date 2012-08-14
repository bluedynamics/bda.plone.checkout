import logging
from zope.interface import (
    Interface,
    implementer,
)
from zope.component import adapter
from zope.publisher.interfaces.browser import IBrowserRequest
from node.utils import instance_property
from .interfaces import ICheckoutAdapter


logger = logging.getLogger('bda.plone.checkout')


@implementer(ICheckoutAdapter)
@adapter(Interface, IBrowserRequest)
class CheckoutAdapter(object):
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
    
    def save(self, providers, widget, data):
        vessel = self.vessel
        for provider in providers:
            fields = data.get(provider.fields_name, dict())
            for key in fields:
                name = '%s.%s' % (key, provider.fields_name)
                vessel[name] = fields[key].extracted
    
    @property
    def vessel(self):
        """``zope.interface.mapping.IWriteMapping`` providing instance.
        
        Form data gets written to this object.
        """
        raise NotImplementedError(u"Abstract CheckoutAdapter does not "
                                  u"implement ``vessel``.")


class NullCheckoutAdapter(CheckoutAdapter):
    """Dummy adapter. provides non persisting write mapping.
    """
    
    @instance_property
    def vessel(self):
        return dict()