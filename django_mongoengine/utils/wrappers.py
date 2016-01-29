from functools import wraps

class ModelDocument(object):
    """
    Document wrapped in django-compatible object
    """

    def __init__(self, document):
        self._document = document
        self._meta = document.get_document_options()
        self._default_manager = document.objects

    def __getattr__(self, name):
        return getattr(self._document, name)

    def __call__(self, *args, **kwargs):
        return self._document(*args, **kwargs)


class WrapDocument(type):
    """
    Wrapper for views to include wrapped `model` attribute
    """

    def __new__(cls, name, bases, attrs):
        document = attrs.get("document")
        if document:
            attrs['model'] = ModelDocument(document)
        return super(WrapDocument, cls).__new__(cls, name, bases, attrs)

class WrapDocumentMixin(object):

    @property
    def model(self):
        return ModelDocument(self.document)

def copy_class(source):
    @wraps(source)
    def decorator(cls):
        for k in source.__dict__:
            if k not in cls.__dict__:
                setattr(cls, k, source.__dict__[k])
        return cls
    return decorator
