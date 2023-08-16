from django.core.exceptions import ImproperlyConfigured

from .detail import DetailView
from .edit import WrapDocumentForm, djmod


class EmbeddedFormMixin(djmod.FormMixin):
    """
    A mixin that provides a way to show and handle a documentform in a request.
    """

    embedded_form_class = None
    embedded_context_name = 'embedded_form'

    def get_form_class(self):
        """
        Returns the form class to use in this view
        """
        if self.embedded_form_class:
            return self.embedded_form_class
        else:
            raise ImproperlyConfigured(
                "No embedded form class provided. An embedded form class must be provided."
            )

    def get_form(self, form_class=None):
        """
        Returns an instance of the form to be used in this view.
        """
        if form_class is None:
            form_class = self.get_form_class()
        return form_class(self.object, **self.get_form_kwargs())

    def get_embedded_object(self):
        """
        Returns an instance of the embedded object. By default this is a freshly created
        instance. Override for something cooler.
        """
        if hasattr(self, 'embedded_object'):
            return self.embedded_object()
        else:
            klass = self.get_form_class()
            return klass.Meta.document()

    def get_form_kwargs(self):
        """
        Returns the keyword arguments for instantiating the form.
        """
        kwargs = super().get_form_kwargs()
        kwargs.update({'instance': self.get_embedded_object()})
        if 'initial' not in kwargs:
            kwargs['initial'] = {}
        return kwargs

    def get_success_url(self):
        object = getattr(self, 'object', self.get_object())
        if self.success_url:
            url = self.success_url % object.__dict__
        else:
            try:
                url = object.get_absolute_url()
            except AttributeError:
                raise ImproperlyConfigured(
                    "No URL to redirect to.  Either provide a url or define"
                    " a get_absolute_url method on the document."
                )
        return url

    def form_valid(self, form):
        self.embedded_object = form.save()
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        self.object = getattr(self, 'object', self.get_object())
        if 'form' in kwargs:
            form = kwargs['form']
        else:
            form = self.get_form(self.get_form_class())
        context[self.embedded_context_name] = form

        return context


class ProcessEmbeddedFormMixin:
    """
    A mixin that processes an embedded form on POST.
    Does not implement any GET handling.
    """

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
        super().post(request, *args, **kwargs)


class BaseEmbeddedFormMixin(EmbeddedFormMixin, ProcessEmbeddedFormMixin):
    """
    A Mixin that handles an embedded form on POST and
    adds the form into the template context.
    """


class EmbeddedDetailView(
    BaseEmbeddedFormMixin,
    DetailView,
    metaclass=WrapDocumentForm,
):
    """
    Renders the detail view of a document and and adds a
    form for an embedded object into the template.

    See BaseEmbeddedFormMixin for details on the form.
    """
