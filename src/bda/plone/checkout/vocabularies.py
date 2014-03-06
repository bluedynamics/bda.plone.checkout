import pycountry
from Products.CMFPlone.utils import safe_unicode
from bda.plone.checkout import message_factory as _


def gender_vocabulary():
    return [('male', _('male', 'Male')),
            ('female', _('female', 'Female'))]


def country_vocabulary():
    """Vocabulary for countries from ISO3166 source.
    """
    return [(it.numeric, safe_unicode(it.name)) for it in pycountry.countries]


def get_pycountry_name(country_id):
    if not country_id:
        return None
    country = pycountry.countries.get(numeric=country_id)
    return country.name
