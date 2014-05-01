
Changelog
=========

0.4dev
------

- Implement ``skip`` property on ``ShippingSelection`` fields provider and
  skip shipping selection if not item in cart is shippable.
  [rnix]

- Use ``bda.plone.checkout.interfaces.ICheckoutSettings`` adapter instead
  of self in ``bda.plone.checkout.browser.form.CheckoutForm`` to handle
  ``skip_payment`` and ``skip_payment_redirect_url``.
  [rnix]

- Remove ``skip_payment`` and ``skip_payment_redirect_url`` attributes
  from ``bda.plone.checkout.interfaces.ICheckoutAdapter`` interface. They exist
  now as functions accepting data uid on
  ``bda.plone.checkout.interfaces.ICheckoutSettings``.
  [rnix]

- Introduce ``bda.plone.checkout.interfaces.ICheckoutSettings`` interface.
  [rnix]

- Implement ``skip`` property on ``PaymentSelection`` fields provider and
  skip payment selection if total cart price is 0.
  [rnix]

- Add ``bda.plone.checkout.interfaces.IFieldsProvider.skip`` attribute.
  [rnix]

- Adopt shipping handling to ``bda.plone.shipping`` >= 0.4.
  [rnix]

- Consider shipping method from cookie in checkout form.
  [rnix]

- Do not rely on acquisition and base link for `terms and conditions`
  on the navigation root. (path/to/navroot/<ID>)

  `ID` is configurable by patching
  ``bda.plone.checkout.browser.form.TERMS_AND_CONDITONS_ID``
  [fRiSi]


0.3
---

- Register pycountry translations and use them.
  [rnix]

- Adopt checkout summary to consider currency and discount.
  [rnix]

- Heading for ``accept_terms`` in checkout form. This better seperates this
  button visually from the rest.
  [thet]

- Prefill the checkout form with defaults from ``ICheckoutFormPresets`` adapter.
  [thet]

- Fix BrowserLayer order precedence.
  [thet]

- introduce ``bda.plone.checkout.ICheckoutFormPresets``.
  [rnix]


0.2
---

- introduce ``skip_payment`` and ``skip_payment_redirect_url`` on
  ``bda.plone.checkout.ICheckoutAdapter`` and consider in
  ``bda.plone.checkout.browser.form.CheckoutForm``.
  [rnix]


0.1
---

- initial work
  [rnix]
