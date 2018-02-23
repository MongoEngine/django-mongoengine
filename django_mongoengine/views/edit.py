from django.utils import six
from django.core.exceptions import ImproperlyConfigured

from django_mongoengine.utils.wrappers import WrapDocument, copy_class
from django_mongoengine.utils.monkey import get_patched_django_module
from django_mongoengine.forms.documents import documentform_factory

from .detail import SingleObjectMixin, SingleObjectTemplateResponseMixin

djmod = get_patched_django_module(
    "django.views.generic.edit",
    model_forms=get_patched_django_module(
        "django.forms.models", modelform_factory=documentform_factory,
    )
)

try:
    FormMixin = djmod.FormMixinBase
except AttributeError:
    # django 1.10
    FormMixin = djmod.FormMixin


class WrapDocumentForm(WrapDocument, FormMixin):
    pass


class DocumentFormFixin(SingleObjectMixin):

    def get_success_url(self):
        """
        Returns the supplied URL.
        """
        if self.success_url:
            url = self.success_url.format(**self.object._data)
        else:
            try:
                url = self.object.get_absolute_url()
            except AttributeError:
                raise ImproperlyConfigured(
                    "No URL to redirect to.  Either provide a url or define"
                    " a get_absolute_url method on the Model.")
        return url


@copy_class(djmod.CreateView)
class CreateView(six.with_metaclass(
        WrapDocumentForm,
        SingleObjectTemplateResponseMixin,
        DocumentFormFixin,
        djmod.BaseCreateView)):
    __doc__  = djmod.CreateView.__doc__


@copy_class(djmod.UpdateView)
class UpdateView(six.with_metaclass(
        WrapDocumentForm,
        SingleObjectTemplateResponseMixin,
        DocumentFormFixin,
        djmod.BaseUpdateView)):
    __doc__  = djmod.UpdateView.__doc__


@copy_class(djmod.DeleteView)
class DeleteView(six.with_metaclass(
        WrapDocumentForm,
        SingleObjectTemplateResponseMixin,
        DocumentFormFixin,
        djmod.BaseDeleteView)):
    __doc__  = djmod.DeleteView.__doc__
