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

try:
    # python3 and new django versions
    from django.utils.encoding import force_text
except ImportError:
    # some very old django versions
    from django.utils.encoding import force_unicode as force_text

try:
    from django.db.models.utils import resolve_callables
except ImportError:
    from .backports import resolve_callables
