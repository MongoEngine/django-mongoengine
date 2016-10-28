import sys

from django.utils import six
from django.db.models.query import QuerySet as DjangoQuerySet

from mongoengine.errors import NotUniqueError
from mongoengine import queryset as qs


class QueryWrapper(object):
    # XXX: copy funcs from django; now it's just wrapper
    select_related = False
    order_by = []

    def __init__(self, q, ordering):
        self.q = q
        self.order_by = ordering or []


class BaseQuerySet(object):
    """
    A base queryset with django-required attributes
    """

    @property
    def model(self):
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

    def exists(self):
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

    get_or_create = DjangoQuerySet.__dict__["get_or_create"]

    _extract_model_params = DjangoQuerySet.__dict__["_extract_model_params"]

    def _create_object_from_params(self, lookup, params):
        """
        Tries to create an object using passed params.
        Used by get_or_create and update_or_create
        """
        try:
            obj = self.create(**params)
            return obj, True
        except NotUniqueError:
            exc_info = sys.exc_info()
            try:
                return self.get(**lookup), False
            except self.model.DoesNotExist:
                pass
            six.reraise(*exc_info)


class QuerySet(BaseQuerySet, qs.QuerySet):
    pass


class QuerySetNoCache(BaseQuerySet, qs.QuerySetNoCache):
    pass


class QuerySetManager(qs.QuerySetManager):
    default = QuerySet
