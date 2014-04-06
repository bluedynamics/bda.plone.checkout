import pycountry
from Products.CMFPlone.utils import safe_unicode
from bda.plone.checkout import message_factory as _
from zope.i18nmessageid import MessageFactory


_c = MessageFactory('iso3166')


def gender_vocabulary():
    return [('male', _('male', 'Male')),
            ('female', _('female', 'Female'))]


def country_vocabulary():
    """Vocabulary for countries from ISO3166 source.
    """
    return [(_.numeric, safe_unicode(_c(_.name))) for _ in pycountry.countries]


def get_pycountry_name(country_id):
    if not country_id:
        return None
    country = pycountry.countries.get(numeric=country_id)
    return _c(country.name)
