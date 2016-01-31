from .document import Document, DynamicDocument
from .queryset import QuerySet

__all__ = ["QuerySet", "Document", "DynamicDocument"]

default_app_config = 'django_mongoengine.apps.DjangoMongoEngineConfig'
