from django.db.models import Model
from django.db.models.base import ModelState

from mongoengine import document as me
from mongoengine.base import metaclasses as mtc

from .utils.patches import serializable_value
from .forms.document_options import DocumentMetaWrapper
from .queryset import QuerySetManager


def django_meta(meta, *top_bases):
    class metaclass(meta):
        def __new__(cls, name, bases, attrs):
            change_bases = len(bases) == 1 and (
                bases[0].__name__ == "temporary_meta"
            )
            if change_bases:
                new_bases = top_bases
            else:
                new_bases = ()
                for b in bases:
                    if getattr(b, 'swap_base', False):
                        new_bases += top_bases
                    else:
                        new_bases += (b,)
            new_cls = meta.__new__(cls, name, new_bases, attrs)
            new_cls._meta = DocumentMetaWrapper(new_cls)
            return new_cls

    return type.__new__(metaclass, 'temporary_meta', (), {})


class DjangoFlavor(object):
    objects = QuerySetManager()
    _default_manager = QuerySetManager()
    serializable_value = serializable_value
    _get_pk_val = Model.__dict__["_get_pk_val"]

    def __init__(self, *args, **kwargs):
        self._state = ModelState()
        self._state.db = self._meta.get("db_alias", me.DEFAULT_CONNECTION_NAME)
        super(DjangoFlavor, self).__init__(*args, **kwargs)

    def _get_unique_checks(self, exclude=None):
        # XXX: source: django/db/models/base.py
        # used in modelform validation
        unique_checks, date_checks = [], []
        return unique_checks, date_checks


class Document(django_meta(mtc.TopLevelDocumentMetaclass,
                           DjangoFlavor, me.Document)):
    swap_base = True


class DynamicDocument(django_meta(mtc.TopLevelDocumentMetaclass,
                                  DjangoFlavor, me.DynamicDocument)):
    swap_base = True


class EmbeddedDocument(django_meta(mtc.DocumentMetaclass,
                                   DjangoFlavor, me.EmbeddedDocument)):
    swap_base = True


class DynamicEmbeddedDocument(django_meta(mtc.DocumentMetaclass,
                                          DjangoFlavor, me.DynamicEmbeddedDocument)):
    swap_base = True
