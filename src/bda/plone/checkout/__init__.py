import logging
from zope.interface import (
    Interface,
    implements,
)
from zope.component import adapts
from .interfaces import IFieldsHandler


logger = logging.getLogger('bda.plone.checkout')


class FieldsHandler(object):
    implements(IFieldsHandler)
    adapts(Interface)
    
    def __init__(self, context):
        self.context = context
    
    def save(self, widget, data):
        raise NotImplementedError(u"Abstract FieldsHandler does not implement "
                                  u"``save``.")
    

class NullFieldsHandler(FieldsHandler):
    """Dummy adapter. does nothing.
    """
    
    def save(self, widget, data):
        logger.info(data[self.context.fields_name].printtree())