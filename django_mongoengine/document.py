#from django.utils import six

from mongoengine import document as me
from mongoengine.base import metaclasses as mtc

from .utils.patches import serializable_value
from .forms.document_options import DocumentMetaWrapper
from .queryset import QuerySetManager

def django_meta(meta, base):
    class metaclass(meta):
        def __new__(cls, name, bases, attrs):
            attrs.setdefault('objects', QuerySetManager())
            attrs.setdefault('_default_manager', QuerySetManager())
            attrs.setdefault('serializable_value', serializable_value)
            change_bases = len(bases) == 1 and (
                bases[0].__name__ == "temporary_meta" or
                bases[0] in [Document, DynamicDocument, EmbeddedDocument]
            )
            if change_bases:
                new_bases = base,
            else:
                new_bases = bases
            new_cls = meta.__new__(cls, name, new_bases, attrs)
            new_cls._meta = DocumentMetaWrapper(new_cls)
            return new_cls

    return type.__new__(metaclass, 'temporary_meta', (), {})

class Document(django_meta(mtc.TopLevelDocumentMetaclass, me.Document)):
    pass

class DynamicDocument(django_meta(mtc.TopLevelDocumentMetaclass, me.DynamicDocument)):
    pass

class EmbeddedDocument(django_meta(mtc.DocumentMetaclass, me.EmbeddedDocument)):
    pass
