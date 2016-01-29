import imp

from django.views.generic import View
from django.utils import six


from mongoengine.queryset import QuerySet

from django_mongoengine.utils.wrappers import WrapDocument

__all__ = [
    "MultipleObjectMixin",
    "BaseListView",
    "ListView",
]

def get_patched_django_module(m, **kwargs):
    from django.views import generic as g
    m = imp.load_module(
        "%s_mongoengine_patched" % m,
        *imp.find_module("list", g.__path__)
    )
    for k, v in kwargs.items():
        setattr(m, k, v)
    return m

djmod = get_patched_django_module("list",
    QuerySet=QuerySet,
)


@six.add_metaclass(WrapDocument)
class MultipleObjectMixin(djmod.MultipleObjectMixin):
    pass


class BaseListView(MultipleObjectMixin, View):
    get = djmod.BaseListView.__dict__["get"]


class ListView(djmod.MultipleObjectTemplateResponseMixin, BaseListView):
    pass
