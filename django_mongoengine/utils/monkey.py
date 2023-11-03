import importlib
import importlib.util
from types import MethodType

from mongoengine.queryset import QuerySet, QuerySetNoCache

from django_mongoengine.fields.djangoflavor import DjangoField


def get_patched_django_module(modname: str, **kwargs):
    # Patch module in-place
    # https://docs.python.org/3/library/importlib.html#importlib-examples
    mod = importlib.import_module(modname)

    spec = importlib.util.spec_from_file_location(mod.__name__, mod.__file__)
    assert spec
    assert spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    for k, v in kwargs.items():
        setattr(module, k, v)
    return module


def patch_mongoengine_field(field_name: str):
    """
    patch mongoengine.[field_name] for comparison support
    becouse it's required in django.forms.models.fields_for_model
    importing using mongoengine internal import cache
    """
    from mongoengine import common

    field = common._import_class(field_name)
    for k in ["__eq__", "__lt__", "__hash__", "attname", "get_internal_type"]:
        if k not in field.__dict__:
            setattr(field, k, DjangoField.__dict__[k])


def patch_typing_support():
    """
    Patch classes to support generic types
    """

    for model in [QuerySet, QuerySetNoCache]:
        model.__class_getitem__ = MethodType(lambda cls, _: cls, QuerySet)  # type: ignore
