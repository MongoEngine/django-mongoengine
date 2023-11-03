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
                attrs['model'] = property(lambda self: self.document)
        return super().__new__(cls, name, bases, attrs)


def copy_class(source):
    def decorator(cls):
        def f(k):
            return k not in cls.__dict__ and not k.startswith("__")

        for k in filter(f, source.__dict__.keys()):
            setattr(cls, k, source.__dict__[k])
        return cls

    return decorator
