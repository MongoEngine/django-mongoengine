# ruff: noqa: F811
from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, Any

from bson.objectid import ObjectId
from django.db.models import Model
from django.db.models.base import ModelState
from mongoengine import DoesNotExist
from mongoengine import document as me
from mongoengine.base import metaclasses as mtc
from mongoengine.errors import FieldDoesNotExist

from .fields import ObjectIdField
from .forms.document_options import DocumentMetaWrapper
from .queryset import QuerySetManager

if TYPE_CHECKING:
    from mongoengine.fields import StringField
    from typing_extensions import Self

# TopLevelDocumentMetaclass is using ObjectIdField to create default pk field,
# if one's not set explicitly.
# We need to know it's not editable and auto_created.
mtc.ObjectIdField = partial(ObjectIdField, editable=False, auto_created=True)


def django_meta(meta, *top_bases):
    class metaclass(meta):
        def __new__(cls, name, bases, attrs):
            change_bases = len(bases) == 1 and (bases[0].__name__ == "temporary_meta")
            if change_bases:
                new_bases = top_bases
            else:
                new_bases = ()
                for b in bases:
                    if getattr(b, "swap_base", False):
                        new_bases += top_bases
                    else:
                        new_bases += (b,)
            new_cls = meta.__new__(cls, name, new_bases, attrs)
            new_cls._meta = DocumentMetaWrapper(new_cls)
            return new_cls

    return type.__new__(metaclass, "temporary_meta", (), {})


class DjangoFlavor:
    id: StringField
    objects = QuerySetManager["Self"]()
    _default_manager = QuerySetManager["Self"]()
    _get_pk_val = Model.__dict__["_get_pk_val"]
    _meta: DocumentMetaWrapper | dict[str, Any]
    DoesNotExist: type[DoesNotExist]

    def __init__(self, *args, **kwargs):
        self._state = ModelState()
        self._state.db = self._meta.get("db_alias", me.DEFAULT_CONNECTION_NAME)
        super().__init__(*args, **kwargs)

    def _get_unique_checks(self, exclude=None):
        # XXX: source: django/db/models/base.py
        # used in modelform validation
        unique_checks, date_checks = [], []
        return unique_checks, date_checks

    def serializable_value(self, field_name):
        """
        Returns the value of the field name for this instance. If the field is
        a foreign key, returns the id value, instead of the object. If there's
        no Field object with this name on the model, the model attribute's
        value is returned directly.

        Used to serialize a field's value (in the serializer, or form output,
        for example). Normally, you would just access the attribute directly
        and not use this method.
        """
        try:
            field = self._meta.get_field(field_name)
        except FieldDoesNotExist:
            return getattr(self, field_name)
        value = field.to_mongo(getattr(self, field.name))
        if isinstance(value, ObjectId):
            return str(value)
        return value


class Document(
    django_meta(
        mtc.TopLevelDocumentMetaclass,
        DjangoFlavor,
        me.Document,
    )
):
    swap_base = True


class DynamicDocument(django_meta(mtc.TopLevelDocumentMetaclass, DjangoFlavor, me.DynamicDocument)):
    swap_base = True


class EmbeddedDocument(django_meta(mtc.DocumentMetaclass, DjangoFlavor, me.EmbeddedDocument)):
    swap_base = True


class DynamicEmbeddedDocument(
    django_meta(mtc.DocumentMetaclass, DjangoFlavor, me.DynamicEmbeddedDocument)
):
    swap_base = True


if TYPE_CHECKING:

    class Document(DjangoFlavor, me.Document):
        ...

    class DynamicDocument(DjangoFlavor, me.DynamicDocument):
        ...

    class EmbeddedDocument(DjangoFlavor, me.EmbeddedDocument):
        _instance: Document

    class DynamicEmbeddedDocument(DjangoFlavor, me.DynamicEmbeddedDocument):
        ...
