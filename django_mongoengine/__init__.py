# -*- coding: utf-8 -*-
"""
    werkzeug
    ~~~~~~~~

    Werkzeug is the Swiss Army knife of Python web development.

    It provides useful classes and functions for any WSGI application to make
    the life of a python web developer much easier.  All of the provided
    classes are independent from each other so you can mix it with any other
    library.


    :copyright: (c) 2011 by the Werkzeug Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
from types import ModuleType
import sys
from django_mongoengine.utils.module import MongoEngine

__version__ = '0.1'


class module(ModuleType):
    """Automatically get attributes from the overloaded MongoEngine class module."""

    def __getattr__(self, name):
        return mongoengine_instance.__getattribute__(name)

    def __dir__(self):
        """Just show what we want to show."""
        result = list(new_module.__all__)
        result.extend(('__file__', '__path__', '__doc__', '__all__',
                       '__docformat__', '__name__', '__path__',
                       '__package__', '__version__'))
        return result

mongoengine_instance = MongoEngine()

# keep a reference to this module so that it's not garbage collected
old_module = sys.modules['django_mongoengine']

# setup the new module and patch it into the dict of loaded modules
new_module = sys.modules['django_mongoengine'] = module('django_mongoengine')
new_module.__dict__.update({
    '__file__':         __file__,
    '__package__':      'django_mongoengine',
    '__path__':         __path__,
    '__doc__':          __doc__,
    '__version__':      __version__,
    '__all__':          mongoengine_instance.__all__,
    '__docformat__':    'restructuredtext en'
})
