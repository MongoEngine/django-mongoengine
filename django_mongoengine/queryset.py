from mongoengine import queryset as qs

from .utils.wrappers import ModelDocument

class QuerySet(qs.QuerySet):
    """
    A base queryset with django-required attributes
    """

    @property
    def model(self):
        return ModelDocument(self._document)
