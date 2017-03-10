# -*- coding: utf-8 -*-
from Products.CMFCore.permissions import setDefaultRoles


# perform checkout
PerformCheckout = 'bda.plone.checkout: Perform Checkout'
setDefaultRoles(PerformCheckout,
                ('Manager', 'Site Administrator', 'Customer'))
