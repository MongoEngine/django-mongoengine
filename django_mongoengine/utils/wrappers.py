
class Manager(object):

    def __init__(self, document):
        self.document = document

    def get_queryset(self):
        return self.document.objects

    def all(self):
        return self.document.objects

class ModelDocument(object):
    """
    Document wrapped in django-compatible object
    """

    def __init__(self, document):
        self._document = document
        self._meta = document.get_document_options()
        self._default_manager = Manager(document)

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
            try:
                attrs['model'] = ModelDocument(document)
            except AttributeError:
                attrs['model'] = property(
                    lambda self: ModelDocument(self.document)
                )
        return super(WrapDocument, cls).__new__(cls, name, bases, attrs)


def copy_class(source):
    def decorator(cls):
        for k in source.__dict__:
            if k not in cls.__dict__:
                setattr(cls, k, source.__dict__[k])
        return cls
    return decorator
