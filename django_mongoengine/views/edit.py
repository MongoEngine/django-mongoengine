from django_mongoengine.utils.wrappers import WrapDocumentMixin
from django_mongoengine.views.utils import get_patched_django_module
from django_mongoengine.forms.documents import documentform_factory

djmod = get_patched_django_module(
    "django.views.generic.edit",
    model_forms=get_patched_django_module(
        "django.forms.models", modelform_factory=documentform_factory,
    )
)

class CreateView(WrapDocumentMixin, djmod.CreateView):
    """
    View for creating an new object instance,
    with a response rendered by template.
    """


class UpdateView(WrapDocumentMixin, djmod.UpdateView):
    """
    View for updating an object,
    with a response rendered by template..
    """


class DeleteView(WrapDocumentMixin, djmod.DeleteView):
    """
    View for deleting an object retrieved with `self.get_object()`,
    with a response rendered by template.
    """
