from yafowil.base import factory
from yafowil.yaml import parse_from_YAML
from yafowil.plone.form import Form
from zope.i18nmessageid import MessageFactory
from ..interfaces import ICheckoutDataAdapter


_ = MessageFactory('bda.plone.checkout')
fields_provider = list()


class FieldsProvider(object):
    fields_template = None
    message_factory = _
    
    def __init__(self, context):
        self.context = context
    
    def extend(self, form):
        fields = parse_from_YAML(self.fields_template, 
                                 self, self.message_factory)
        form[fields.name] = fields


class CheckoutForm(Form):
    
    def prepare(self):
        action = self.context.absolute_url() + '/@@checkout'
        self.form = factory('#form', name='checkout', props={'action': action})
        for provider in fields_provider:
            provider.extend(self.form)
        self.form['submit'] = factory('submit', props={
            'label': _('save', 'Save'),
            'action': 'save',
            'handler': self.save})
    
    def save(self, widget, data):
        ICheckoutDataAdapter(self.context).save(widget, data)