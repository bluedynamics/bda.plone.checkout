from yafowil.base import (
    factory,
    ExtractionError,
    UNSET,
)
from yafowil.yaml import parse_from_YAML
from yafowil.plone.form import Form
from zope.i18nmessageid import MessageFactory
from ..interfaces import IFieldsHandler


_ = MessageFactory('bda.plone.checkout')
fields_provider = list()


CHECKOUT = 0
CONFIRM = 1

class FormContext(object):
    
    @property
    def form_context(self):
        return self.request.get('checkout_confirm') and CONFIRM or CHECKOUT
    
    @property
    def mode(self):
        return self.form_context is CONFIRM and 'display' or 'edit'
    
    def get_value(self, widget, data):
        return self.request.get(widget.dottedpath, UNSET)


class FieldsProvider(FormContext):
    fields_template = None
    fields_name = ''
    message_factory = _
    
    def __init__(self, context, request):
        self.context = context
        self.request = request
    
    def extend(self, form):
        fields = parse_from_YAML(self.fields_template, 
                                 self, self.message_factory)
        form[self.fields_name] = fields


class PersonalData(FieldsProvider):
    fields_template = 'bda.plone.checkout.browser:forms/personal_data.yaml'
    fields_name = 'personal_data'
    
    @property
    def gender_vocabulary(self):
        return [('-', '-'),
                ('male', _('male', 'Male')),
                ('female', _('female', 'Female'))]

fields_provider.append(PersonalData)


class BillingAddress(FieldsProvider):
    fields_template = 'bda.plone.checkout.browser:forms/billing_address.yaml'
    fields_name = 'billing_address'

fields_provider.append(BillingAddress)


class DeliveryAddress(FieldsProvider):
    fields_template = 'bda.plone.checkout.browser:forms/delivery_address.yaml'
    fields_name = 'delivery_address'
    
    def conditional_required(self, widget, data):
        if data.parent['alternative_delivery'].extracted and not data.extracted:
            raise ExtractionError(widget.attrs['conditional_required'])
        return data.extracted

fields_provider.append(DeliveryAddress)


class PaymentSelection(FieldsProvider):
    fields_template = 'bda.plone.checkout.browser:forms/payment_selection.yaml'
    fields_name = 'payment_selection'
    
    @property
    def payment_vocabulary(self):
        return [('invoice', _('invoice', 'Invoice')),
                ('credit_card', _('credit_card', 'Credit card'))]

fields_provider.append(PaymentSelection)


class OrderComment(FieldsProvider):
    fields_template = 'bda.plone.checkout.browser:forms/order_comment.yaml'
    fields_name = 'order_comment'

fields_provider.append(OrderComment)


class CheckoutForm(Form, FormContext):
    
    action_resource = '@@checkout'
    
    def prepare(self):
        self.form = factory('#form', name='checkout', props={
            'action': self.form_action})
        
        for fields_factory in fields_provider:
            fields_factory(self.context, self.request).extend(self.form)
        
        self.form['submit'] = factory('submit', props={
            'label': _('save', 'Save'),
            'action': 'save',
            'handler': self.save,
            'next': self.next})
    
    def save(self, widget, data):
        for fields_factory in fields_provider:
            provider = fields_factory(self.context, self.request)
            IFieldsHandler(provider).save(widget, data)
    
    def next(self, request):
        self.request['checkout_confirm'] = '1'
        self.prepare()
        return self.form(request=request)
