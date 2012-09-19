from yafowil.base import (
    factory,
    ExtractionError,
    UNSET,
)
from yafowil.yaml import parse_from_YAML
from yafowil.plone.form import Form
from zExceptions import Redirect
from zope.interface import implementer
from zope.component import getMultiAdapter
from zope.i18nmessageid import MessageFactory
from bda.plone.payment import Payments
from ..interfaces import (
    IFieldsProvider,
    ICheckoutAdapter,
)

_ = MessageFactory('bda.plone.checkout')


class ProviderRegistry(object):
    
    def __init__(self):
        self.providers = list()
    
    def add(self, factory):
        self.providers.append(factory)
    
    def __iter__(self):
        return self.providers.__iter__()

provider_registry = ProviderRegistry()


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


@implementer(IFieldsProvider)
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


class CartSummary(FieldsProvider):
    fields_name = 'cart_summary'
    
    def extend(self, form):
        if not self.form_context == CONFIRM:
            return
        compound = form[self.fields_name] = factory('compound', props={
            'structural': True})
        compound['heading'] = factory('tag', props={
            'structural': True,
            'tag': 'h2',
            'text': _('heading_cart_summary', 'Cart')})
        compound['overview'] = factory('tag', props={
            'structural': True,
            'class': 'cart_overview',
            'tag': 'div',
            'text': self.context.restrictedTraverse('@@cart_overview')()})

provider_registry.add(CartSummary)


class PersonalData(FieldsProvider):
    fields_template = 'bda.plone.checkout.browser:forms/personal_data.yaml'
    fields_name = 'personal_data'
    
    @property
    def gender_vocabulary(self):
        return [('-', '-'),
                ('male', _('male', 'Male')),
                ('female', _('female', 'Female'))]

provider_registry.add(PersonalData)


class BillingAddress(FieldsProvider):
    fields_template = 'bda.plone.checkout.browser:forms/billing_address.yaml'
    fields_name = 'billing_address'

provider_registry.add(BillingAddress)


class DeliveryAddress(FieldsProvider):
    fields_template = 'bda.plone.checkout.browser:forms/delivery_address.yaml'
    fields_name = 'delivery_address'
    
    def conditional_required(self, widget, data):
        if data.parent['alternative_delivery'].extracted and not data.extracted:
            raise ExtractionError(widget.attrs['conditional_required'])
        return data.extracted
    
    def get_alternative_delivery(self, widget, data):
        return widget.dottedpath in self.request
    
    @property
    def alternative_delivery_vocab(self):
        return {
            True: _('yes', 'Yes'),
            False: _('no', 'No'),
            UNSET: _('not set', 'not set'),
        }

provider_registry.add(DeliveryAddress)


class PaymentSelection(FieldsProvider):
    fields_template = 'bda.plone.checkout.browser:forms/payment_selection.yaml'
    fields_name = 'payment_selection'
    
    @property
    def payments(self):
        return Payments(self.context)
    
    @property
    def payment_vocabulary(self):
        return self.payments.vocab
    
    def get_payment(self, widget, data):
        return self.request.get(widget.dottedpath, self.payments.default)

provider_registry.add(PaymentSelection)


class OrderComment(FieldsProvider):
    fields_template = 'bda.plone.checkout.browser:forms/order_comment.yaml'
    fields_name = 'order_comment'

provider_registry.add(OrderComment)


class CheckoutForm(Form, FormContext):
    
    action_resource = '@@checkout'
    
    def prepare(self):
        self.form = factory('#form', name='checkout', props={
            'action': self.form_action})
        for fields_factory in provider_registry:
            fields_factory(self.context, self.request).extend(self.form)
        # checkout data input
        if not self.request.get('checkout_confirm') \
          and not self.request.get('action.checkout.finish'):
            self.form['checkout_back'] = factory('submit', props={
                'label': _('back', 'Back'),
                'action': 'checkout_back',
                'handler': None,
                'next': self.checkout_back,
                'skip': True})
            self.form['next'] = factory('submit', props={
                'label': _('next', 'Next'),
                'action': 'next',
                'handler': None,
                'next': self.checkout_summary})
        # checkout confirmation
        else:
            self.form['confirm_back'] = factory('submit', props={
                'label': _('back', 'Back'),
                'action': 'confirm_back',
                'handler': None,
                'next': self.confirm_back})
            self.form['finish'] = factory('submit', props={
                'label': _('finish', 'Finish'),
                'action': 'finish',
                'handler': self.finish,
                'next': self.checkout_done})
    
    def checkout_back(self, request):
        raise Redirect('%s/@@cart' % self.context.absolute_url())
    
    def confirm_back(self, request):
        self.prepare()
        return self.form(request=request)
    
    def checkout_summary(self, request):
        self.request['checkout_confirm'] = '1'
        self.prepare()
        return self.form(request=request)
    
    def checkout_done(self, request):
        raise Redirect(self.finish_redirect_url)
    
    def finish(self, widget, data):
        providers = [fields_factory(self.context, self.request) \
                     for fields_factory in provider_registry]
        checkout_adapter = getMultiAdapter((self.context, self.request),
                                           ICheckoutAdapter)
        checkout_adapter.save(providers, widget, data)
        checkout_adapter.clear()
        p_name = data.fetch('checkout.payment_selection.payment').extracted
        payments = Payments(self.context)
        payment = payments.get(p_name)
        #if not payment.deferred:
        #    checkout_adapter.notify()
        self.finish_redirect_url = payment.init_url()
