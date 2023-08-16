from .detail import DetailView
from .edit import CreateView, DeleteView, UpdateView
from .embedded import EmbeddedDetailView
from .list import ListView

__all__ = [
    "ListView",
    "DetailView",
    "EmbeddedDetailView",
    "CreateView",
    "UpdateView",
    "DeleteView",
]
