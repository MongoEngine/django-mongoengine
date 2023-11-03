from __future__ import annotations

from typing_extensions import Self

from mongoengine import DoesNotExist
from mongoengine import document as me
from mongoengine.fields import StringField

from .queryset import QuerySetManager
from .forms.document_options import DocumentMetaWrapper

class DjangoFlavor:
    id: StringField
    # https://github.com/sbdchd/mongo-types#getting-objects-to-work
    # Types moved to pyi, to avoid monkey-patching QuerySet.
    objects: QuerySetManager[Self]
    _meta: DocumentMetaWrapper
    _default_manager: QuerySetManager[Self]
    DoesNotExist: type[DoesNotExist]

class Document(DjangoFlavor, me.Document):
    ...

class DynamicDocument(DjangoFlavor, me.DynamicDocument):
    ...

class EmbeddedDocument(DjangoFlavor, me.EmbeddedDocument):
    _instance: Document

class DynamicEmbeddedDocument(DjangoFlavor, me.DynamicEmbeddedDocument):
    ...
