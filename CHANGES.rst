
Changelog
=========

0.3dev
------

- Heading for accept_terms form in checkout. This better seperates this button
  visually from the rest.
  [thet]

- Prefill the checkout form with defaults from ICheckoutFormPresets adapter.
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
