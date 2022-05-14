import importlib
import importlib.util


def get_patched_django_module(modname: str, **kwargs):
    # Patch module in-place
    # https://docs.python.org/3/library/importlib.html#importlib-examples
    mod = importlib.import_module(modname)

    spec = importlib.util.spec_from_file_location(mod.__name__, mod.__file__)
    assert spec
    assert spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    for k, v in kwargs.items():
        setattr(module, k, v)
    return module
