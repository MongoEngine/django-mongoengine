from __future__ import absolute_import

from .list import ListView
from .detail import DetailView
from .embedded import EmbeddedDetailView
from .edit import CreateView, UpdateView, DeleteView

__all__ = [
    "ListView",
    "DetailView",
    "EmbeddedDetailView",
    "CreateView", "UpdateView", "DeleteView",
]
