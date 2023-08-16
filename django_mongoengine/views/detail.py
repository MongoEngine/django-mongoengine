from django.core.exceptions import ImproperlyConfigured
from django.views.generic import detail as djmod
from django.views.generic.base import TemplateResponseMixin, View

from django_mongoengine.utils.wrappers import WrapDocument, copy_class


class SingleObjectMixin(djmod.SingleObjectMixin, metaclass=WrapDocument):
    document = None

    def get_context_object_name(self, obj):
        """
        Get the name to use for the object.
        """
        if self.context_object_name:
            return self.context_object_name
        elif hasattr(obj, '_meta'):
            return obj._meta.model_name
        else:
            return None


class SingleObjectTemplateResponseMixin(TemplateResponseMixin):
    template_name_field = None
    template_name_suffix = '_detail'

    def get_template_names(self):
        """
        Return a list of template names to be used for the request. May not be
        called if render_to_response is overridden. Returns the following list:

        * the value of ``template_name`` on the view (if provided)
        * the contents of the ``template_name_field`` field on the
          object instance that the view is operating upon (if available)
        * ``<app_label>/<model_name><template_name_suffix>.html``
        """
        try:
            names = super().get_template_names()
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

            # The least-specific option is the default <app>/<model>_detail.html;
            # only use this if the object in question is a model.
            opts = None
            if hasattr(self.object, '_meta'):
                opts = self.object._meta
            elif hasattr(self, 'model') and self.model is not None:
                opts = self.model._meta
            if opts:
                names.append(
                    "%s/%s%s.html" % (opts.app_label, opts.model_name, self.template_name_suffix)
                )

            # If we still haven't managed to find any template names, we should
            # re-raise the ImproperlyConfigured to alert the user.
            if not names:
                raise

        return names


@copy_class(djmod.BaseDetailView)
class BaseDetailView(SingleObjectMixin, View):
    __doc__ = djmod.BaseDetailView.__doc__


class DetailView(SingleObjectTemplateResponseMixin, BaseDetailView):
    pass
