import imp
import importlib

def get_patched_django_module(modname, **kwargs):
    parent, m = modname.rsplit(".", 1)
    path = importlib.import_module(parent).__path__
    mod = imp.load_module(
        ".".join([__name__, modname.replace(".", "_")]),
        *imp.find_module(m, path)
    )
    for k, v in kwargs.items():
        setattr(mod, k, v)
    return mod
