from drf_spectacular import openapi
from drf_spectacular.openapi import OpenApiTypes, build_basic_type

from django.db import models
from django_mongoengine.forms.document_options import PkWrapper
from mongoengine.fields import BaseField
from rest_framework import serializers

SUPPORTED_FIELDS = (PkWrapper, BaseField)


class AutoSchema(openapi.AutoSchema):
    """
    Schema supporting basic MongoEngine integration,
    while falling back to default for not django-mongoengine fields.
    """

    def _map_model_field(self, model_field, direction):
        if isinstance(model_field, SUPPORTED_FIELDS):
            if hasattr(model_field, "get_internal_type"):
                internal_type = getattr(models, model_field.get_internal_type())
                field_cls = serializers.ModelSerializer.serializer_field_mapping.get(internal_type)
                if field_cls:
                    return self._map_serializer_field(field_cls(), direction)
            return build_basic_type(OpenApiTypes.STR)
        return super()._map_model_field(model_field, direction)
