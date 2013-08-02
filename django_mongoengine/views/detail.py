from django.core.exceptions import ImproperlyConfigured
from django.http import Http404
from django.utils.encoding import smart_str
from django.utils.translation import ugettext as _
from django.views.generic.base import TemplateResponseMixin, View

from django_mongoengine.forms.utils import get_document_options

from mongoengine.queryset import DoesNotExist


class SingleDocumentMixin(object):
    """
    Provides the ability to retrieve a single object for further manipulation.
    """
    document = None
    queryset = None
    slug_field = 'slug'
    context_object_name = None
    slug_url_kwarg = 'slug'
    pk_url_kwarg = 'pk'

    def get_object(self, queryset=None):
        """
        Returns the object the view is displaying.

        By default this requires `self.queryset` and a `pk` or `slug` argument
        in the URLconf, but subclasses can override this to return any object.
        """
        # Use a custom queryset if provided; this is required for subclasses
        # like DateDetailView
        if queryset is None:
            queryset = self.get_queryset()

        # Next, try looking up by primary key.
        pk = self.kwargs.get(self.pk_url_kwarg, None)
        slug = self.kwargs.get(self.slug_url_kwarg, None)
        if pk is not None:
            queryset = queryset.filter(pk=pk)

        # Next, try looking up by slug.
        elif slug is not None:
            slug_field = self.get_slug_field()
            queryset = queryset.filter(**{slug_field: slug})

        # If none of those are defined, it's an error.
        else:
            raise AttributeError(u"Generic detail view %s must be called with "
                                 u"either an object pk or a slug."
                                 % self.__class__.__name__)

        try:
            obj = queryset.get()
        except DoesNotExist:
            opts = get_document_options(queryset._document)
            raise Http404(_(u"No %(verbose_name)s found matching the query") %
                          {'verbose_name': opts.verbose_name})
        return obj

    def get_queryset(self):
        """
        Get the queryset to look an object up against. May not be called if
        `get_object` is overridden.
        """
        if self.queryset is None:
            if self.document:
                return self.document.objects()
            else:
                raise ImproperlyConfigured(u"%(cls)s is missing a queryset. Define "
                                           u"%(cls)s.document, %(cls)s.queryset, or override "
                                           u"%(cls)s.get_queryset()." % {
                                                'cls': self.__class__.__name__
                                                })
        return self.queryset.clone()

    def get_slug_field(self):
        """
        Get the name of a slug field to be used to look up by slug.
        """
        return self.slug_field

    def get_context_object_name(self, obj):
        """
        Get the name to use for the object.
        """
        if self.context_object_name:
            return self.context_object_name
        elif hasattr(obj, '_meta'):
            opts = get_document_options(obj)
            return smart_str(opts.object_name.lower())
        else:
            return None

    def get_context_data(self, **kwargs):
        context = kwargs
        context_object_name = self.get_context_object_name(self.object)
        if context_object_name:
            context[context_object_name] = self.object
        return context


class BaseDetailView(SingleDocumentMixin, View):
    def get(self, request, **kwargs):
        self.object = self.get_object()
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)


class SingleDocumentTemplateResponseMixin(TemplateResponseMixin):
    template_name_field = None
    template_name_suffix = '_detail'

    def get_template_names(self):
        """
        Return a list of template names to be used for the request. Must return
        a list. May not be called if get_template is overridden.
        """
        try:
            names = super(SingleDocumentTemplateResponseMixin, self).get_template_names()
        except ImproperlyConfigured:
            # If template_name isn't specified, it's not a problem --
            # we just start with an empty list.
            names = []

        # If self.template_name_field is set, grab the value of the field
        # of that name from the object; this is the most specific template
        # name, if given.
        if self.object and self.template_name_field:
            name = getattr(self.object, self.template_name_field, None)
            if name:
                names.insert(0, name)

        # The least-specific option is the default <app>/<document>_detail.html;
        # only use this if the object in question is a document.
        if hasattr(self.object, '_meta'):
            doc_cls = self.object.__class__
        elif hasattr(self, 'document') and hasattr(self.document, '_meta'):
            doc_cls = self.document
        else:
            if names:
                return names
            raise ImproperlyConfigured("No object or document class associated with this view")

        # Get any superclasses if needed
        doc_classes = [doc_cls]
        for doc_cls in doc_classes:
            opts = get_document_options(doc_cls)
            name = "%s/%s%s.html" % (
                opts.app_label,
                opts.object_name.lower(),
                self.template_name_suffix
            )
            if name not in names:
                names.append(name)

        # Basic template form: templates/_types.html
        names.append("{}s.html".format(self.template_name_suffix))
        return names


class DetailView(SingleDocumentTemplateResponseMixin, BaseDetailView):
    """
    Render a "detail" view of an object.

    By default this is a document instance looked up from `self.queryset`, but the
    view will support display of *any* object by overriding `self.get_object()`.
    """
