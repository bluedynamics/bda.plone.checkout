from bda.plone.checkout import message_factory as _
from plone.base.utils import safe_text
from zope.i18nmessageid import MessageFactory

import pycountry

_c = MessageFactory("iso3166-1")


def gender_vocabulary():
    return [
        ("male", _("male", default=u"Male")),
        ("female", _("female", default=u"Female")),
    ]


AVAILABLE_COUNTRIES = [
    (country.numeric, safe_text(_c(country.name))) for country in pycountry.countries
]
# patch this list to modify available countries
ENABLED_COUNTRIES = [
    "040",  # Austria
    "756",  # Switzerland
    "276",  # Germany
    "380",  # Italy
]


def country_vocabulary():
    """Vocabulary for countries from ISO3166 source.
    """
    countries_numeric = pycountry.countries.indices["numeric"]
    ret = list()
    for country in ENABLED_COUNTRIES:
        if country in countries_numeric:
            ret.append((country, safe_text(_c(countries_numeric[country].name))))
    return ret


def get_pycountry_name(country_id):
    if not country_id:
        return None
    country = pycountry.countries.get(numeric=country_id)
    return _c(country.name)
