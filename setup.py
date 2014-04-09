"""Setup script for nose-sfd"""
from setuptools import setup
from setuptools import find_packages

import sfd

setup(
    name='nose-sfd',
    version=sfd.__version__,

    description='nose plugin for testing Django projects in a faster way.',
    long_description=open('README.rst').read(),
    keywords='nose, django, tests',

    author=sfd.__author__,
    author_email=sfd.__email__,
    url=sfd.__url__,

    packages=find_packages(),
    classifiers=[
        'Framework :: Django',
        'Development Status :: 5 - Production/Stable',
        'Programming Language :: Python',
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Topic :: Software Development :: Testing',
        'License :: OSI Approved :: GNU Library or Lesser General Public License (LGPL)'],
    license=sfd.__license__,
    include_package_data=True,

    install_requires='nose>=0.10',
    entry_points={
        'nose.plugins': [
            'sfd = sfd.sfd:SimpleFastDjango',
        ]
    }
)
