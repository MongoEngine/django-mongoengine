try:
    from django.db.models.utils import resolve_callables
except ImportError:
    from .backports import resolve_callables
