try:
    from collections import OrderedDict
except ImportError:
    from ordereddict import OrderedDict

try:
    # django >= 1.4
    from django.utils.timezone import now as datetime_now
except ImportError:
    from datetime import datetime
    datetime_now = datetime.now

from django.utils.encoding import force_str

try:
    from django.db.models.utils import resolve_callables
except ImportError:
    from .backports import resolve_callables
