from django_mongoengine.utils.isinstance import patched_isinstance


def patch_drf_spectacular():
    try:
        import drf_spectacular.openapi
    except ImportError:
        pass
    else:
        drf_spectacular.openapi.isinstance = patched_isinstance
