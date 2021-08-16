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

# SVG for buttons
SVG_PREV = """<svg class="bi bi-chevron-left" width="1em" height="1em" viewBox="0 0 16 16" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                <path fill-rule="evenodd" d="M11.354 1.646a.5.5 0 0 1 0 .708L5.707 8l5.647 5.646a.5.5 0 0 1-.708.708l-6-6a.5.5 0 0 1 0-.708l6-6a.5.5 0 0 1 .708 0z"/>
              </svg>
           """
SVG_NEXT = """<svg class="bi bi-chevron-right" width="1em" height="1em" viewBox="0 0 16 16" fill="currentColor" xmlns="http: // www.w3.org/2000/svg">
                <path fill-rule = "evenodd" d = "M4.646 1.646a.5.5 0 0 1 .708 0l6 6a.5.5 0 0 1 0 .708l-6 6a.5.5 0 0 1-.708-.708L10.293 8 4.646 2.354a.5.5 0 0 1 0-.708z"/>
              </svg >
           """
SVG_FINISH = """<svg class="bi bi-credit-card" width="1em" height="1em" viewBox="0 0 16 16" fill="currentColor" xmlns="http://www.w3.org/2000/svg">
                  <path fill-rule="evenodd" d="M14 3H2a1 1 0 0 0-1 1v8a1 1 0 0 0 1 1h12a1 1 0 0 0 1-1V4a1 1 0 0 0-1-1zM2 2a2 2 0 0 0-2 2v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H2z"/>
                  <rect width="3" height="3" x="2" y="9" rx="1"/>
                  <path d="M1 5h14v2H1z"/>
                </svg>
             """


class FormContext(object):
    @property
    def form_context(self):
        if (
            self.request.get("checkout_confirm") is not None
            or self.request.get("action.checkout.finish") is not None
        ):
            return CONFIRM
        return CHECKOUT

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


checkout_button_factories = list()


def default_checkout_button_factory(view):
    view.form["form-controls"]["checkout_back"] = factory(
        "button",
        props={
            "type": "submit",
            "text": _("back", "${icon} Back", mapping={"icon": SVG_PREV}),
            "action": "checkout_back",
            "class": "btn btn-secondary me-3",
            "handler": None,
            "next": view.checkout_back,
            "skip": True,
        },
    )
    view.form["form-controls"]["next"] = factory(
        "button",
        props={
            "type": "submit",
            "text": _("next", "Next ${icon}", mapping={"icon": SVG_NEXT}),
            "action": "next",
            "class": "btn btn-primary",
            "handler": None,
            "next": view.checkout_summary,
        },
    )


checkout_button_factories.append(default_checkout_button_factory)


confirmation_button_factories = list()


def default_confirmation_button_factory(view):
    view.form["form-controls"]["confirm_back"] = factory(
        "button",
        props={
            "type": "submit",
            "text": _("back", "${icon} Back", mapping={"icon": SVG_PREV}),
            "action": "confirm_back",
            "class": "btn btn-secondary me-3",
            "handler": None,
            "next": view.confirm_back,
        },
    )
    view.form["form-controls"]["finish"] = factory(
        "button",
        props={
            "type": "submit",
            "text": _("finish", "Order now ${icon}", mapping={"icon": SVG_FINISH}),
            "class": "prevent_if_no_longer_available btn btn-primary",
            "action": "finish",
            "handler": view.finish,
            "next": view.checkout_done,
        },
    )


confirmation_button_factories.append(default_confirmation_button_factory)




class CheckoutForm(Form, FormContext):
    action_resource = "@@checkout"
    # in order to provide your own registry, subclass CheckoutForm and and
    # override ``provider_registry``
    provider_registry = provider_registry
    checkout_button_factories = checkout_button_factories
    confirmation_button_factories = confirmation_button_factories

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
        self.form["form-controls"] = factory(
            "div",
            props={
                "structural": True,
                "class_add": "mb-3 d-flex"
            }
        )
        if checkout:
            for button_factory in self.checkout_button_factories:
                button_factory(self)
        # checkout confirmation
        else:
            for button_factory in self.confirmation_button_factories:
                button_factory(self)

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
        checkout_settings = ICheckoutSettings(self.context)
        if checkout_settings.skip_payment(uid):
            checkout_adapter.clear_session()
            self.finish_redirect_url = checkout_settings.skip_payment_redirect_url(uid)
        else:
            p_name = data.fetch("checkout.payment_selection.payment").extracted
            payments = Payments(self.context)
            payment = payments.get(p_name)
            if payment.clear_session:
                checkout_adapter.clear_session()
            self.finish_redirect_url = payment.init_url(str(uid))
        event = CheckoutDone(self.context, self.request, uid)
        notify(event)
