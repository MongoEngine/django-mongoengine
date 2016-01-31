from django.utils import six

from mongoengine.queryset import QuerySet

from django_mongoengine.utils.wrappers import WrapDocument
from django_mongoengine.utils.monkey import get_patched_django_module

__all__ = [
    "MultipleObjectMixin",
    "ListView",
]

djmod = get_patched_django_module("django.views.generic.list",
    QuerySet=QuerySet,
)

@six.add_metaclass(WrapDocument)
class MultipleObjectMixin(djmod.MultipleObjectMixin):
    pass

@six.add_metaclass(WrapDocument)
class MultipleObjectTemplateResponseMixin(djmod.MultipleObjectTemplateResponseMixin):
    pass

class ListView(MultipleObjectTemplateResponseMixin, djmod.BaseListView):
    pass
