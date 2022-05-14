import importlib

from mongoengine.queryset import QuerySet

from django_mongoengine.utils.monkey import get_patched_django_module


def test_monkey_patch():
    patched = get_patched_django_module("django.views.generic.list", QuerySet=QuerySet)

    assert patched.QuerySet is QuerySet

    original = importlib.import_module("django.views.generic.list")

    assert original.QuerySet is not QuerySet
