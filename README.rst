bda.plone.checkout
==================


Create translations
-------------------

::

    cd src/bda/plone/checkout/
    
    i18ndude rebuild-pot --pot locales/bda.plone.checkout.pot \
        --merge locales/manual.pot --create bda.plone.checkout .
    
    i18ndude sync --pot locales/bda.plone.checkout.pot \
        locales/de/LC_MESSAGES/bda.plone.checkout.po
