def resolve_callables(mapping):
    """
    Generate key/value pairs for the given mapping where the values are
    evaluated if they're callable.
    """
    # backport from django-3.2
    # after we drop support for django below 3.2, this can be removed
    for k, v in mapping.items():
        yield k, v() if callable(v) else v
