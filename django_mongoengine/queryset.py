from __future__ import annotations

from typing import TYPE_CHECKING, Generic, TypeVar

from django.db.models.query import QuerySet as DjangoQuerySet
from django.db.models.utils import resolve_callables
from mongoengine import queryset as qs
from mongoengine.errors import NotUniqueError

from .utils.monkey import patch_typing_support

if TYPE_CHECKING:
    from .document import Document

_M = TypeVar("_M", bound="Document")

patch_typing_support()


class QueryWrapper:
    # XXX: copy funcs from django; now it's just wrapper
    select_related = False
    order_by = []

    def __init__(self, q, ordering):
        self.q = q
        self.order_by = ordering or []


class BaseQuerySet(Generic[_M]):
    """
    A base queryset with django-required attributes
    """

    @property
    def model(self) -> type[_M]:
        return self._document

    @property
    def query(self):
        return QueryWrapper(self._query, self._ordering)

    @property
    def _prefetch_related_lookups(self):
        # Originally used in django for prefetch_related(),
        # see https://docs.djangoproject.com/en/1.9/ref/models/querysets/#prefetch-related
        # returning empty list to presume that no query prefetch is required
        return []

    def iterator(self):
        return self

    def get_queryset(self):
        return self

    def latest(self, field_name):
        return self.order_by("-" + field_name).first()

    def earliest(self, field_name):
        return self.order_by(field_name).first()

    def exists(self) -> bool:
        return bool(self)

    def _clone(self):
        return self.clone()

    @property
    def ordered(self):
        """
        Returns True if the QuerySet is ordered -- i.e. has an order_by()
        clause or a default ordering on the model.
        """
        if self._ordering:
            return True
        elif self._document._meta.ordering:
            return True
        else:
            return False

    def get_or_create(self, defaults=None, **kwargs):
        """
        Look up an object with the given kwargs, creating one if necessary.
        Return a tuple of (object, created), where created is a boolean
        specifying whether an object was created.
        """
        try:
            return self.get(**kwargs), False
        except self.model.DoesNotExist:
            params = self._extract_model_params(defaults, **kwargs)
            # Try to create an object using passed params.
            try:
                params = dict(resolve_callables(params))
                return self.create(**params), True
            except NotUniqueError:
                try:
                    return self.get(**kwargs), False
                except self.model.DoesNotExist:
                    pass
                raise

    def update_or_create(self, defaults=None, **kwargs):
        """
        Look up an object with the given kwargs, updating one with defaults
        if it exists, otherwise create a new one.
        Return a tuple (object, created), where created is a boolean
        specifying whether an object was created.
        """
        defaults = defaults or {}
        self._for_write = True
        obj, created = self.get_or_create(defaults, **kwargs)
        if created:
            return obj, created
        for k, v in resolve_callables(defaults):
            setattr(obj, k, v)
        obj.save()
        return obj, False

    _extract_model_params = DjangoQuerySet.__dict__["_extract_model_params"]


class QuerySet(BaseQuerySet[_M], qs.QuerySet[_M]):
    pass


class QuerySetNoCache(BaseQuerySet[_M], qs.QuerySetNoCache[_M]):
    pass


class QuerySetManager(Generic[_M], qs.QuerySetManager):
    default = QuerySet
    if TYPE_CHECKING:

        def __get__(self, instance: object, cls: type[_M]) -> QuerySet[_M]:
            ...
