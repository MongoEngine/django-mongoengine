from mongoengine import document as me

from .forms.document_options import DocumentMetaWrapper
from .queryset import QuerySet

class DocumentMixin(object):

    @classmethod
    def get_document_options(cls):
        return DocumentMetaWrapper(cls)


class Document(me.Document, DocumentMixin):
    """Abstract document with extra helpers in the queryset class"""
    meta = {
        'abstract': True,
        'queryset_class': QuerySet,
    }



class DynamicDocument(me.DynamicDocument, DocumentMixin):
    """Abstract Dynamic document with extra helpers in the queryset class"""
    meta = {
        'abstract': True,
        'queryset_class': QuerySet,
    }
