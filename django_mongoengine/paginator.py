from django.core.paginator import Paginator
from django.utils.functional import cached_property


class Paginator(Paginator):
    @cached_property
    def count(self):
        try:
            return self.object_list.count()
        except TypeError:
            return len(self.object_list)
