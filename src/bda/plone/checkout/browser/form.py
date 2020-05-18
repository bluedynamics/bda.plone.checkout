from bda.plone.cart import cookie
from bda.plone.cart.cart import get_data_provider
from bda.plone.cart.shipping import Shippings
from bda.plone.checkout import CheckoutDone
from bda.plone.checkout import message_factory as _
from bda.plone.checkout.interfaces import CheckoutError
from bda.plone.checkout.interfaces import ICheckoutAdapter
from bda.plone.checkout.interfaces import ICheckoutFormPresets
from bda.plone.checkout.interfaces import ICheckoutSettings
from bda.plone.checkout.interfaces import IFieldsProvider
from bda.plone.checkout.vocabularies import country_vocabulary
from bda.plone.checkout.vocabularies import gender_vocabulary
from bda.plone.payment import Payments
from yafowil.base import ExtractionError
from yafowil.base import factory
from yafowil.base import UNSET
from yafowil.plone.form import Form
from yafowil.yaml import parse_from_YAML
from zExceptions import Redirect
from zope.component import getMultiAdapter
from zope.event import notify
from zope.i18n import translate
from zope.interface import implementer

import plone.api
import transaction


TERMS_AND_CONDITONS_ID = "agb"


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
        confirm = self.request.get("checkout_confirm") or self.request.get(
            "action.checkout.finish"
        )
        return confirm and CONFIRM or CHECKOUT

    @property
    def mode(self):
        return self.form_context is CONFIRM and "display" or "edit"


@implementer(IFieldsProvider)
class FieldsProvider(FormContext):
    fields_template = None
    fields_name = ""
    message_factory = _
    ignore_on_save = False
    skip = False

    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.preset_adapter = getMultiAdapter(
            (self.context, self.request), ICheckoutFormPresets
        )

    def get_value(self, widget, data):
        """Function to fetch form field default values.

        Special case in checkout form is that form fields might get hidden mode
        """
        default = self.preset_adapter.get_value(widget.dottedpath)
        ret = None
        # XXX: improve, looks odd
        if "checkbox" in widget.blueprints:
            # for selected checkboxes, not the value but only the input name
            # (dottedpath) is in request.form, otherwise they are completly
            # ommited.
            ret = widget.dottedpath in self.request or default
        else:
            ret = self.request.get(widget.dottedpath, default)
        return ret

    def extend(self, form):
        if self.skip:
            return
        fields = parse_from_YAML(self.fields_template, self, self.message_factory)
        form[self.fields_name] = fields


class CartSummary(FieldsProvider):
    fields_name = "cart_summary"

    def extend(self, form):
        if not self.form_context == CONFIRM:
            return
        compound = form[self.fields_name] = factory(
            "compound", props={"structural": True}
        )
        compound["heading"] = factory(
            "tag",
            props={
                "structural": True,
                "tag": "h2",
                "text": _("heading_cart_summary", "Cart"),
            },
        )
        compound["overview"] = factory(
            "tag",
            props={
                "structural": True,
                "class": "cart_overview checkout_cart_overview clearfix",
                "tag": "div",
                "text": self.context.restrictedTraverse("@@cart_overview")(),
            },
        )


provider_registry.add(CartSummary)


class PersonalData(FieldsProvider):
    fields_template = "bda.plone.checkout.browser:forms/personal_data.yaml"
    fields_name = "personal_data"

    @property
    def gender_vocabulary(self):
        return [("-", "")] + gender_vocabulary()


provider_registry.add(PersonalData)


class BillingAddress(FieldsProvider):
    fields_template = "bda.plone.checkout.browser:forms/billing_address.yaml"
    fields_name = "billing_address"

    @property
    def country_vocabulary(self):
        return country_vocabulary()


provider_registry.add(BillingAddress)


class DeliveryAddress(BillingAddress):
    fields_template = "bda.plone.checkout.browser:forms/delivery_address.yaml"
    fields_name = "delivery_address"

    def conditional_required(self, widget, data):
        if data.parent["alternative_delivery"].extracted and not data.extracted:
            raise ExtractionError(widget.attrs["conditional_required"])
        return data.extracted

    @property
    def hidden_class(self):
        if self.form_context is CHECKOUT:
            return ""
        name = "checkout.delivery_address.alternative_delivery"
        if self.request.get(name) is None:
            return "hidden"
        return ""

    @property
    def alternative_delivery_vocab(self):
        return {
            True: _("yes", "Yes"),
            False: _("no", "No"),
            UNSET: _("not set", "not set"),
        }


provider_registry.add(DeliveryAddress)


class ShippingSelection(FieldsProvider):
    fields_template = "bda.plone.checkout.browser:forms/shipping_selection.yaml"
    fields_name = "shipping_selection"

    @property
    def skip(self):
        cart_data = get_data_provider(self.context, self.request)
        return not cart_data.include_shipping_costs

    @property
    def shippings(self):
        return Shippings(self.context)

    @property
    def shipping_vocabulary(self):
        vocab = list()
        for sh in self.shippings.shippings:
            if not sh.available:
                continue
            if sh.description:
                label = translate(sh.label, context=self.request)
                desc = translate(sh.description, context=self.request)
                title = "%s (%s)" % (label, desc)
            else:
                title = translate(sh.label, context=self.request)
            vocab.append((sh.sid, title))
        return vocab

    def get_shipping(self, widget, data):
        request = self.request
        from_request = request.get(widget.dottedpath)
        from_cookie = request.cookies.get("shipping_method")
        # got selection from request which differs from cookie, set cookie
        if from_request and from_cookie != from_request:
            request.response.setCookie(
                "shipping_method", from_request, quoted=False, path="/"
            )
        # no shipping from request or cookie, return default
        if not from_request and not from_cookie:
            return self.shippings.default
        # shipping from cookie, but not from request, return cookie
        if from_cookie and not from_request:
            return from_cookie
        # return from request
        return from_request


provider_registry.add(ShippingSelection)


class PaymentSelection(FieldsProvider):
    fields_template = "bda.plone.checkout.browser:forms/payment_selection.yaml"
    fields_name = "payment_selection"

    @property
    def skip(self):
        cart_data = get_data_provider(self.context, self.request)
        return not cart_data.total

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
    fields_template = "bda.plone.checkout.browser:forms/order_comment.yaml"
    fields_name = "order_comment"

    @property
    def hidden_class(self):
        if self.form_context is CHECKOUT:
            return ""
        name = "checkout.order_comment.comment"
        if not self.request.get(name):
            return "hidden"
        return ""


provider_registry.add(OrderComment)


class AcceptTermsAndConditions(FieldsProvider):
    fields_template = "bda.plone.checkout.browser:forms/accept_terms.yaml"
    fields_name = "accept_terms_and_conditions"
    ignore_on_save = True

    @property
    def accept_label(self):
        nav_root = plone.api.portal.get_navigation_root(self.context)
        base = nav_root.absolute_url()
        # XXX: url from config
        tac_url = "{}/{}".format(base, TERMS_AND_CONDITONS_ID)
        tac_label = _("terms_and_conditions", "Terms and conditions")
        tac_label = translate(tac_label, context=self.request)
        tac_link = (
            u'<a href="{}"'
            u'   class="terms_and_conditions pat-plone-modal"'
            u'   data-pat-plone-modal="width: 75%;">{}</a>'
        ).format(tac_url, tac_label)
        tac_text = _(
            "terms_and_conditions_text",
            "I have read and accept the ${terms_and_conditions}",
            mapping={"terms_and_conditions": tac_link},
        )
        return tac_text

    @property
    def mode(self):
        if self.request.get("action.checkout.finish") or self.form_context is CONFIRM:
            return "edit"
        return "skip"

    def validate_accept(self, widget, data):
        if not data.extracted:
            raise ExtractionError(
                _(
                    "error_accept_terms_and_conditiond",
                    "Please accept our terms and conditions.",
                )
            )
        return data.extracted


provider_registry.add(AcceptTermsAndConditions)


class CheckoutForm(Form, FormContext):
    action_resource = "@@checkout"
    # in order to provide your own registry, subclass CheckoutForm and and
    # override ``provider_registry``
    provider_registry = provider_registry

    def prepare(self):
        if not cookie.read(self.request):
            raise Redirect(self.context.absolute_url())
        checkout = self.form_context is CHECKOUT
        if checkout:
            form_method, form_class = "post", "mode_edit"
        else:
            form_method, form_class = "post", "mode_display"
        self.form = factory(
            "#form",
            name="checkout",
            props={
                "action": self.form_action,
                "class_add": form_class,
                "method": form_method,
            },
        )
        for fields_factory in self.provider_registry:
            fields_factory(self.context, self.request).extend(self.form)
        # checkout data input
        if checkout:
            self.form["checkout_back"] = factory(
                "submit",
                props={
                    "label": _("back", "Back"),
                    "action": "checkout_back",
                    "class_add": "btn btn-secondary",
                    "handler": None,
                    "next": self.checkout_back,
                    "skip": True,
                },
            )
            self.form["next"] = factory(
                "submit",
                props={
                    "label": _("next", "Next"),
                    "action": "next",
                    "class_add": "btn btn-primary",
                    "handler": None,
                    "next": self.checkout_summary,
                },
            )
        # checkout confirmation
        else:
            self.form["confirm_back"] = factory(
                "submit",
                props={
                    "label": _("back", "Back"),
                    "action": "confirm_back",
                    "handler": None,
                    "next": self.confirm_back,
                },
            )
            self.form["finish"] = factory(
                "submit",
                props={
                    "class": "prevent_if_no_longer_available context",
                    "label": _("finish", "Order now"),
                    "action": "finish",
                    "handler": self.finish,
                    "next": self.checkout_done,
                },
            )

    def checkout_back(self, request):
        raise Redirect("%s/@@cart" % self.context.absolute_url())

    def confirm_back(self, request):
        self.prepare()
        return self.form(request=request)

    def checkout_summary(self, request):
        self.request["checkout_confirm"] = "1"
        self.prepare()
        return self.form(request=request)

    def checkout_done(self, request):
        transaction.commit()
        raise Redirect(self.finish_redirect_url)

    def finish(self, widget, data):
        providers = [
            fields_factory(self.context, self.request)
            for fields_factory in self.provider_registry
        ]
        to_adapt = (self.context, self.request)
        checkout_adapter = getMultiAdapter(to_adapt, ICheckoutAdapter)
        try:
            uid = checkout_adapter.save(providers, widget, data)
        except CheckoutError:
            transaction.abort()
            self.checkout_back(self.request)
        checkout_adapter.clear_session()
        checkout_settings = ICheckoutSettings(self.context)
        if checkout_settings.skip_payment(uid):
            self.finish_redirect_url = checkout_settings.skip_payment_redirect_url(uid)
        else:
            p_name = data.fetch("checkout.payment_selection.payment").extracted
            payments = Payments(self.context)
            payment = payments.get(p_name)
            self.finish_redirect_url = payment.init_url(str(uid))
        event = CheckoutDone(self.context, self.request, uid)
        notify(event)
