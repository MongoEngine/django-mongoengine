class WrapDocument(type):
    """
    Wrapper for views to include wrapped `model` attribute
    """

    def __new__(cls, name, bases, attrs):
        document = attrs.get("document")
        if document:
            try:
                attrs['model'] = document
            except AttributeError:
                attrs['model'] = property(
                    lambda self: self.document
                )
        return super(WrapDocument, cls).__new__(cls, name, bases, attrs)


def copy_class(source):
    def decorator(cls):
        f = lambda (k, v): (
            k not in cls.__dict__ and not k.startswith("__")
        )
        for k, v in filter(f, source.__dict__.items()):
            setattr(cls, k, v)
        return cls
    return decorator
