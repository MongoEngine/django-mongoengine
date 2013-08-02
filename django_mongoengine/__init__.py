"""
    django_mongoengine
    ~~~~~~~~~~~~~~~~~~

    Django and MongoEngine integration giving easy forms and generic views
    integration.
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
    '__file__': __file__,
    '__package__': 'django_mongoengine',
    '__path__': __path__,
    '__doc__': __doc__,
    '__version__': __version__,
    '__all__': mongoengine_instance.__all__,
    '__docformat__': 'restructuredtext en'
})

extra_mod_mixins = ('connection', 'document', 'fields', 'queryset', 'signals')
for mixin in extra_mod_mixins:
    sys.modules['django_mongoengine.%s' % mixin] = getattr(
        mongoengine_instance, mixin)
