import imp
import importlib

def get_patched_django_module(modname, **kwargs):
    parent, m = modname.rsplit(".", 1)
    path = importlib.import_module(parent).__path__
    m = imp.load_module(
        "django_mongoengine.monkey.%s" % modname,
        *imp.find_module(m, path)
    )
    for k, v in kwargs.items():
        setattr(m, k, v)
    return m
