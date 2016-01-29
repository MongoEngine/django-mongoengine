from django_mongoengine.forms.utils import get_document_options

class ModelDocument(object):
    """
    Document wrapped in django-compatible object
    """

    def __init__(self, document):
        self._document = document
        self._meta = get_document_options(document)
        self._default_manager = document.objects

    def __getattr__(self, name):
        return getattr(self._document, name)


class WrapDocument(type):
    """
    Wrapper for views to include wrapped `model` attribute
    """

    def __new__(cls, name, bases, attrs):
        if 'document' in attrs:
            attrs['model'] = ModelDocument(attrs['document'])
        return super(WrapDocument, cls).__new__(cls, name, bases, attrs)
