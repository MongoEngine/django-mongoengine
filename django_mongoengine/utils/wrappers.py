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


class WrapDocument(object):
    """
    Wrapper for views to include wrapped `model` attribute
    """

    def __init__(self, *args, **kwargs):
        try:
            self.model = ModelDocument(self.document)
        except AttributeError:
            pass
