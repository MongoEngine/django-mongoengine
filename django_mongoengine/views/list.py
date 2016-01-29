from django.views.generic import View

from mongoengine.queryset import QuerySet

from django_mongoengine.utils.wrappers import WrapDocument
from .utils import get_patched_django_module

__all__ = [
    "MultipleObjectMixin",
    "BaseListView",
    "ListView",
]

djmod = get_patched_django_module("django.views.generic.list",
    QuerySet=QuerySet,
)


class MultipleObjectMixin(djmod.MultipleObjectMixin, WrapDocument):
    pass


class BaseListView(MultipleObjectMixin, View):
    get = djmod.BaseListView.__dict__["get"]


class ListView(djmod.MultipleObjectTemplateResponseMixin, BaseListView):
    pass
