from mongoengine.queryset import QuerySet

from django_mongoengine.paginator import Paginator
from django_mongoengine.utils.monkey import get_patched_django_module
from django_mongoengine.utils.wrappers import WrapDocument, copy_class

__all__ = [
    "MultipleObjectMixin",
    "ListView",
]

djmod = get_patched_django_module(
    "django.views.generic.list",
    QuerySet=QuerySet,
)


class MultipleObjectMixin(djmod.MultipleObjectMixin, metaclass=WrapDocument):
    paginator_class = Paginator


class MultipleObjectTemplateResponseMixin(
    djmod.MultipleObjectTemplateResponseMixin,
    metaclass=WrapDocument,
):
    pass


@copy_class(djmod.ListView)
class ListView(MultipleObjectTemplateResponseMixin, djmod.BaseListView):
    __doc__ = djmod.ListView.__doc__
    paginator_class = Paginator
