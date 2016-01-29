#from django.views.generic.base import ContextMixin
#from django.utils import six

from django_mongoengine.forms.documents import documentform_factory

#from django_mongoengine.utils.wrappers import WrapDocument

from .utils import get_patched_django_module

djmod = get_patched_django_module(
    "django.views.generic.edit",
    model_forms=get_patched_django_module(
        "django.forms.models", modelform_factory=documentform_factory,
    )
)


class CreateView(djmod.CreateView):
    """
    View for creating an new object instance,
    with a response rendered by template.
    """


class UpdateView(djmod.UpdateView):
    """
    View for updating an object,
    with a response rendered by template..
    """


class DeleteView(djmod.DeleteView):
    """
    View for deleting an object retrieved with `self.get_object()`,
    with a response rendered by template.
    """
