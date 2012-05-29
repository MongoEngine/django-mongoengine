from django.conf import settings
from django.template.loader import render_to_string

from debug_toolbar.panels import DebugPanel
import operation_tracker

_ = lambda x: x


class MongoDebugPanel(DebugPanel):
    """Panel that shows information about MongoDB operations (including stack)

    Adapted from https://github.com/hmarr/django-debug-toolbar-mongo
    """
    name = 'MongoDB'
    has_content = True

    def __init__(self, *args, **kwargs):
        """
        Install the tracker
        """
        super(MongoDebugPanel, self).__init__(*args, **kwargs)
        operation_tracker.install_tracker()

    def process_request(self, request):
        operation_tracker.reset()

    def nav_title(self):
        return 'MongoDB'

    def nav_subtitle(self):
        attrs = ['queries', 'inserts', 'updates', 'removes']
        ops = sum(sum((1 for o in getattr(operation_tracker, a)
                         if not o['internal']))
                         for a in attrs)
        total_time = sum(sum(o['time'] for o in getattr(operation_tracker, a))
                         for a in attrs)
        return '{0} operations in {1:.2f}ms'.format(ops, total_time)

    def title(self):
        return 'MongoDB Operations'

    def url(self):
        return ''

    def content(self):
        context = self.context.copy()
        context['queries'] = operation_tracker.queries
        context['inserts'] = operation_tracker.inserts
        context['updates'] = operation_tracker.updates
        context['removes'] = operation_tracker.removes
        context['slow_query_limit'] = getattr(settings, 'MONGODB_DEBUG_PANEL_SLOW_QUERY_LIMIT', 100)
        return render_to_string('mongodb-panel.html', context)
