from __future__ import absolute_import

from django.views.generic.base import View, TemplateView, RedirectView

from .detail import DetailView
from .edit import FormView, CreateView, UpdateView, DeleteView, EmbeddedDetailView
from .list import ListView


class GenericViewError(Exception):
    """A problem in a generic view."""
    pass
