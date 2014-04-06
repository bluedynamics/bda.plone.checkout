import pycountry
from Products.CMFPlone.utils import safe_unicode
from bda.plone.checkout import message_factory as _
from zope.i18nmessageid import MessageFactory


_c = MessageFactory('iso3166')


def gender_vocabulary():
    return [('male', _('male', 'Male')),
            ('female', _('female', 'Female'))]


AVAILABLE_COUNTRIES = [
    (country.numeric, safe_unicode(_c(country.name))) \
        for country in pycountry.countries
]
# patch this list to modify available countries
ENABLED_COUNTRIES = [
    '040', # Austria
    '756', # Switzerland
    '276', # Germany
    '380', # Italy
]


def country_vocabulary():
    """Vocabulary for countries from ISO3166 source.
    """
    ret = list()
    for cid, name in AVAILABLE_COUNTRIES:
        if cid in ENABLED_COUNTRIES:
            ret.append((cid, name))
    return ret


def get_pycountry_name(country_id):
    if not country_id:
        return None
    country = pycountry.countries.get(numeric=country_id)
    return _c(country.name)
