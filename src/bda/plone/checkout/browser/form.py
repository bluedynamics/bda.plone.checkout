import transaction
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
from zope.i18n import translate
from bda.plone.cart import readcookie
from bda.plone.payment import Payments
from bda.plone.shipping import Shippings
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
        confirm = self.request.get('checkout_confirm') or \
                  self.request.get('action.checkout.finish')
        return confirm and CONFIRM or CHECKOUT

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
    ignore_on_save = False

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
        return [('-', ''),
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
    def hidden_class(self):
        if self.form_context is CHECKOUT:
            return ''
        name = 'checkout.delivery_address.alternative_delivery'
        if self.request.get(name) is None:
            return 'hidden'
        return ''

    @property
    def alternative_delivery_vocab(self):
        return {
            True: _('yes', 'Yes'),
            False: _('no', 'No'),
            UNSET: _('not set', 'not set'),
        }

provider_registry.add(DeliveryAddress)


class ShippingSelection(FieldsProvider):
    fields_template = 'bda.plone.checkout.browser:forms/shipping_selection.yaml'
    fields_name = 'shipping_selection'

    @property
    def shippings(self):
        return Shippings(self.context)

    @property
    def shipping_vocabulary(self):
        return self.shippings.vocab

    def get_shipping(self, widget, data):
        return self.request.get(widget.dottedpath, self.shippings.default)

provider_registry.add(ShippingSelection)


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

    @property
    def hidden_class(self):
        if self.form_context is CHECKOUT:
            return ''
        name = 'checkout.order_comment.comment'
        if not self.request.get(name):
            return 'hidden'
        return ''

provider_registry.add(OrderComment)


class AcceptTermsAndConditions(FieldsProvider):
    fields_template = 'bda.plone.checkout.browser:forms/accept_terms.yaml'
    fields_name = 'accept_terms_and_conditions'
    ignore_on_save = True

    @property
    def accept_label(self):
        # XXX: url from config
        tac_url = '%s/agb' % self.context.absolute_url()
        tac_label = _('terms_and_conditions', 'Terms and conditions')
        tac_label = translate(tac_label, context=self.request)
        tac_link = '<a href="%s" class="terms_and_consitions">%s</a>'
        tac_link = tac_link % (tac_url, tac_label)
        tac_text = _('terms_and_conditions_text',
                     'I have read and accept the ${terms_and_conditions}',
                     mapping={'terms_and_conditions': tac_link})
        return tac_text

    @property
    def mode(self):
        if self.request.get('action.checkout.finish') \
          or self.form_context is CONFIRM:
            return 'edit'
        return 'skip'

    def validate_accept(self, widget, data):
        if not data.extracted:
            raise ExtractionError(_('error_accept_terms_and_conditiond',
                                    'Please accept our terms and conditions.'))
        return data.extracted

provider_registry.add(AcceptTermsAndConditions)


class CheckoutForm(Form, FormContext):
    action_resource = '@@checkout'
    # in order to provide your own registry, subclass CheckoutForm and and
    # override ``provider_registry``
    provider_registry = provider_registry

    def prepare(self):
        if not readcookie(self.request):
            raise Redirect(self.context.absolute_url())
        checkout = self.form_context is CHECKOUT
        form_class = checkout and 'mode_edit' or 'mode_display'
        self.form = factory('#form', name='checkout', props={
            'action': self.form_action,
            'class_add': form_class})
        for fields_factory in self.provider_registry:
            fields_factory(self.context, self.request).extend(self.form)
        # checkout data input
        if checkout:
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
                'class': 'prevent_if_no_longer_available',
                'label': _('finish', 'Order now'),
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
        transaction.commit()
        raise Redirect(self.finish_redirect_url)

    def finish(self, widget, data):
        providers = [fields_factory(self.context, self.request) \
                     for fields_factory in self.provider_registry]
        to_adapt = (self.context, self.request)
        checkout_adapter = getMultiAdapter(to_adapt, ICheckoutAdapter)
        uid = checkout_adapter.save(providers, widget, data)
        checkout_adapter.clear_session()
        p_name = data.fetch('checkout.payment_selection.payment').extracted
        payments = Payments(self.context)
        payment = payments.get(p_name)
        self.finish_redirect_url = payment.init_url(str(uid))
