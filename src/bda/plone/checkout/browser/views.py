from yafowil.base import factory
from yafowil.yaml import parse_from_YAML
from yafowil.plone.form import Form
from zope.i18nmessageid import MessageFactory
from ..interfaces import IFieldsHandler


_ = MessageFactory('bda.plone.checkout')
fields_provider = list()


class FieldsProvider(object):
    fields_template = None
    fields_name = ''
    message_factory = _
    
    def __init__(self, context):
        self.context = context
    
    def extend(self, form):
        fields = parse_from_YAML(self.fields_template, 
                                 self, self.message_factory)
        form[self.fields_name] = fields


class Address(FieldsProvider):
    
    @property
    def gender_vocabulary(self):
        return [('-', '-'),
                ('male', _('male', 'Male')),
                ('female', _('female', 'Female'))]


class BillingAddress(Address):
    fields_template = 'bda.plone.checkout.browser:forms/billing_address.yaml'
    fields_name = 'billing_address'

fields_provider.append(BillingAddress)


class DeliveryAddress(Address):
    fields_template = 'bda.plone.checkout.browser:forms/delivery_address.yaml'
    fields_name = 'delivery_address'

fields_provider.append(DeliveryAddress)


#class PaymentSelection(FieldsProvider):
#    fields_template = 'bda.plone.checkout.browser:forms/payment_selection.yaml'
#    fields_name = 'payment_selection'

#fields_provider.append(PaymentSelection)


class CheckoutForm(Form):
    
    def prepare(self):
        action = self.context.absolute_url() + '/@@checkout'
        self.form = factory('#form', name='checkout', props={'action': action})
        for provider in fields_provider:
            provider(self.context).extend(self.form)
        self.form['submit'] = factory('submit', props={
            'label': _('save', 'Save'),
            'action': 'save',
            'handler': self.save})
    
    def save(self, widget, data):
        for provider in fields_provider:
            IFieldsHandler(provider(self.context)).save(widget, data)