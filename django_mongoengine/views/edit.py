from django.utils import six
from django_mongoengine.utils.wrappers import WrapDocument
from django_mongoengine.utils.monkey import get_patched_django_module
from django_mongoengine.forms.documents import documentform_factory

from .detail import SingleObjectTemplateResponseMixin

djmod = get_patched_django_module(
    "django.views.generic.edit",
    model_forms=get_patched_django_module(
        "django.forms.models", modelform_factory=documentform_factory,
    )
)

class WrapDocumentForm(WrapDocument, djmod.FormMixinBase):
    pass


class CreateView(six.with_metaclass(
        WrapDocumentForm,
        SingleObjectTemplateResponseMixin,
        djmod.BaseCreateView)):
    """
    View for creating an new object instance,
    with a response rendered by template.
    """


class UpdateView(six.with_metaclass(
        WrapDocumentForm,
        SingleObjectTemplateResponseMixin,
        djmod.BaseUpdateView)):
    """
    View for updating an object,
    with a response rendered by template..
    """


class DeleteView(six.with_metaclass(
        WrapDocumentForm,
        SingleObjectTemplateResponseMixin,
        djmod.BaseDeleteView)):
    """
    View for deleting an object retrieved with `self.get_object()`,
    with a response rendered by template.
    """
