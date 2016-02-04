#from django.utils import six

from mongoengine import document as me
from mongoengine.base import metaclasses as mtc

from .forms.document_options import DocumentMetaWrapper
from .queryset import QuerySetManager

def django_meta(meta, *bases):
    class metaclass(meta):
        def __new__(cls, name, this_bases, attrs):
            attrs.setdefault('objects', QuerySetManager())
            attrs.setdefault('_default_manager', QuerySetManager())
            new_cls = meta.__new__(cls, name, bases, attrs)
            new_cls._meta = DocumentMetaWrapper(new_cls)
            return new_cls

    return type.__new__(metaclass, 'temporary_meta', (), {})

class Document(django_meta(mtc.TopLevelDocumentMetaclass, me.Document)):
    pass

class DynamicDocument(django_meta(mtc.TopLevelDocumentMetaclass, me.DynamicDocument)):
    pass

class EmbeddedDocument(django_meta(mtc.DocumentMetaclass, me.EmbeddedDocument)):
    pass
