from setuptools import find_packages
from setuptools import setup

import os


version = "2.0.dev0"
shortdesc = "Checkout"
longdesc = open(os.path.join(os.path.dirname(__file__), "README.rst")).read()
longdesc += open(os.path.join(os.path.dirname(__file__), "CHANGES.rst")).read()
longdesc += open(os.path.join(os.path.dirname(__file__), "LICENSE.rst")).read()


setup(
    name="bda.plone.checkout",
    version=version,
    description=shortdesc,
    long_description=longdesc,
    classifiers=[
        "Framework :: Plone",
        "Framework :: Plone :: 5.1",
        "Framework :: Plone :: 5.2",
        "Programming Language :: Python",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: GNU General Public License (GPL)",
    ],
    author="BlueDynamics Alliance",
    author_email="dev@bluedynamics.com",
    license="GNU General Public Licence",
    packages=find_packages("src"),
    package_dir={"": "src"},
    namespace_packages=["bda", "bda.plone"],
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        "setuptools",
        "Plone",
        "bda.plone.cart",
        "bda.plone.payment",
        "pycountry",
        "yafowil.plone",
    ],
    extras_require={"test": ["plone.app.testing"]},
)
