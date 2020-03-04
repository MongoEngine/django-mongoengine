from django.core.paginator import Paginator
from django.utils.functional import cached_property


class Paginator(Paginator):

    @cached_property
    def count(self):
        return self.object_list.count()
