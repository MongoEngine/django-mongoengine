from django.utils import six
from django_mongoengine.utils.wrappers import WrapDocument, copy_class
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


@copy_class(djmod.CreateView)
class CreateView(six.with_metaclass(
        WrapDocumentForm,
        SingleObjectTemplateResponseMixin,
        djmod.BaseCreateView)):
    __doc__  = djmod.CreateView.__doc__


@copy_class(djmod.UpdateView)
class UpdateView(six.with_metaclass(
        WrapDocumentForm,
        SingleObjectTemplateResponseMixin,
        djmod.BaseUpdateView)):
    __doc__  = djmod.UpdateView.__doc__


@copy_class(djmod.DeleteView)
class DeleteView(six.with_metaclass(
        WrapDocumentForm,
        SingleObjectTemplateResponseMixin,
        djmod.BaseDeleteView)):
    __doc__  = djmod.DeleteView.__doc__
