from .document import Document, DynamicDocument, EmbeddedDocument
from .queryset import QuerySet

__all__ = ["QuerySet", "Document", "DynamicDocument", "EmbeddedDocument"]

default_app_config = 'django_mongoengine.apps.DjangoMongoEngineConfig'
