from .document import Document, DynamicDocument, DynamicEmbeddedDocument, EmbeddedDocument
from .queryset import QuerySet, QuerySetNoCache

__all__ = [
    "QuerySet",
    "QuerySetNoCache",
    "Document",
    "DynamicDocument",
    "EmbeddedDocument",
    "DynamicEmbeddedDocument",
]

try:
    from django import VERSION as _django_version

    if _django_version < (3, 2):
        default_app_config = "django_mongoengine.apps.DjangoMongoEngineConfig"
except ImportError:
    pass
