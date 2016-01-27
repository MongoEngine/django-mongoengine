from django.views.generic import list as djangolist
from django.views.generic import View
from django.core.exceptions import ImproperlyConfigured
from django.utils import six


from mongoengine.queryset import QuerySet
from django_mongoengine.forms.utils import get_document_options

__all__ = [
    "MultipleObjectMixin",
    "BaseListView",
    "MultipleObjectTemplateResponseMixin",
    "ListView",
]

class MultipleObjectMixin(djangolist.MultipleObjectMixin):

    def get_queryset(self):
        """
        Return the list of items for this view.

        The return value must be an iterable and may be an instance of
        `QuerySet` in which case `QuerySet` specific behavior will be enabled.
        """
        if self.queryset is not None:
            queryset = self.queryset
            if isinstance(queryset, QuerySet):
                queryset = queryset.all()
        elif self.model is not None:
            queryset = self.model.objects.all()
        else:
            raise ImproperlyConfigured(
                "%(cls)s is missing a QuerySet. Define "
                "%(cls)s.model, %(cls)s.queryset, or override "
                "%(cls)s.get_queryset()." % {
                    'cls': self.__class__.__name__
                }
            )
        ordering = self.get_ordering()
        if ordering:
            if isinstance(ordering, six.string_types):
                ordering = (ordering,)
            queryset = queryset.order_by(*ordering)

        return queryset

class BaseListView(MultipleObjectMixin, View):
    get = djangolist.BaseListView.__dict__["get"]

class MultipleObjectTemplateResponseMixin(djangolist.MultipleObjectTemplateResponseMixin):

    def get_template_names(self):
        """
        Return a list of template names to be used for the request. Must return
        a list. May not be called if render_to_response is overridden.
        """
        try:
            names = super(MultipleObjectTemplateResponseMixin, self).get_template_names()
        except ImproperlyConfigured:
            # If template_name isn't specified, it's not a problem --
            # we just start with an empty list.
            names = []

        # If the list is a queryset, we'll invent a template name based on the
        # app and model name. This name gets put at the end of the template
        # name list so that user-supplied names override the automatically-
        # generated ones.
        if hasattr(self.object_list, '_document'):
            opts = get_document_options(self.object_list._document)
            names.append("%s/%s%s.html" % (opts.app_label, opts.model_name, self.template_name_suffix))

        return names


class ListView(MultipleObjectTemplateResponseMixin, BaseListView):
    pass
