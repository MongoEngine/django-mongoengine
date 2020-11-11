from functools import singledispatch
from itertools import chain

from django.db.models import Field
from mongoengine.fields import BaseField

from django_mongoengine.forms.document_options import PkWrapper


def patched_isinstance(obj, class_or_tuple):
    return isinstance(obj, _patch(class_or_tuple))


patched_isinstance.__doc__ = isinstance.__doc__ + """

Patched to accept not only Django classes, but also DjangoMongoEngine.
"""


@singledispatch
def _patch(arg):
    if arg in _classes_mapping:
        return (arg, *_classes_mapping[arg])
    return arg


@_patch.register
def _(arg: tuple):
    return arg + tuple(
        chain(
            _classes_mapping[c]
            for c in arg
            if c in _classes_mapping
        )
    )


_classes_mapping = {
    Field: (BaseField, PkWrapper),
}
