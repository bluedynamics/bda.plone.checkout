==================
bda.plone.checkout
==================

Checkout process and forms for ``bda.plone.shop``.


Installation
============

This package is part of the ``bda.plone.shop`` stack. Please refer to
`bda.plone.shop <https://github.com/bluedynamics/bda.plone.shop>`_ for
installation instructions.


Customizing the checkout form
=============================

To customize the checkout form you'll typically start off with your own
form having a custom ``provider_registry``.

You'll use the ``FieldsProvider`` objects that you're happy with and replace
those that need an adaption.

In this example, we'll add an additional field ``uid`` to the ``PersonalData``
provider an re-use the others.::

    from zope.i18nmessageid import MessageFactory
    from bda.plone.checkout.browser import form as coform


    _ = MessageFactory('my.package')
    my_provider_registry = coform.ProviderRegistry()


    class MyPersonalData(coform.PersonalData):
        fields_template = 'my.package.shop:forms/personal_data.yaml'
        message_factory = _


    my_provider_registry.add(coform.CartSummary)
    my_provider_registry.add(MyPersonalData)
    my_provider_registry.add(coform.BillingAddress)
    my_provider_registry.add(coform.DeliveryAddress)
    my_provider_registry.add(coform.ShippingSelection)
    my_provider_registry.add(coform.PaymentSelection)
    my_provider_registry.add(coform.OrderComment)
    my_provider_registry.add(coform.AcceptTermsAndConditions)


    class MyCheckoutForm(coform.CheckoutForm):
        """Customized checkout form to add UID field for company.
        """
        provider_registry = my_provider_registry

Copy ``bda/plone/checkout/browser/forms/personal_data.yaml`` to
``my/package/shop/forms/personal_data.yaml`` and make your changes.

This package uses `Yet Another FOrm WIdget Library`_ (`YAFOWIL`)
for rendering the checkout form.

.. _`Yet Another FOrm WIdget Library`: http://docs.yafowil.info/

We'll append a new field `uid` at the end of the ``personal data``
section::

    ...
    - company:
        factory: "#field:text"
        value: context.get_value
        props:
            label: i18n:label_company:Company
            display_proxy: True
        mode: expr:context.mode
    - uid:
        factory: "#field:text"
        value: context.get_value
        props:
            label: i18n:label_companyuid:UID Number
            display_proxy: True
        mode: expr:context.mode 

(NOTE: it's not possible to mix i18n domains within a yaml file so
you're better off to add you translations to a separtate
``bda.plone.checkout.po`` file in your package's locales)

Now register your customized form by overriding the browser page
for your browserlayer or skinlayer::

    <browser:page
      for="*"
      name="checkoutform"
      class=".checkout.MyCheckoutForm"
      permission="zope2.View"
      layer=".browser.interfaces.IThemeSpecific" />

.. NOTE:: Your new field will automatically be included in the order data.

    However, by default, it will not show up in order emails, the order export
    (``@@exportorders``) or the order summary (``@@orders``).
    See `bda.plone.orders`_ for instructions how to add them there.

    .. _`bda.plone.orders`: https://github.com/bluedynamics/bda.plone.orders


Create translations
===================

::

    $ cd src/bda/plone/checkout/
    $ ./i18n.sh


Contributors
============

- Robert Niederreiter (Author)
- Peter Holzer
- Harald Friessnegger
