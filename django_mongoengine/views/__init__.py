from __future__ import absolute_import

from .detail import DetailView
from .edit import CreateView, UpdateView, DeleteView, EmbeddedDetailView
from .list import ListView

__all__ = [
    "DetailView", "CreateView", "UpdateView", "DeleteView", "EmbeddedDetailView",
    "ListView",
]

class GenericViewError(Exception):
    """A problem in a generic view."""
    pass
