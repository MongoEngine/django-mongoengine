from mongoengine import queryset as qs


class QuerySet(qs.QuerySet):
    """
    A base queryset with django-required attributes
    """

    @property
    def model(self):
        return self._document


class QuerySetManager(qs.QuerySetManager):
    default = QuerySet

    def all(self):
        return self.get_queryset()
