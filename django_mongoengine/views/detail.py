from django.views.generic.base import View
from django.views.generic import detail as djmod


from django_mongoengine.utils.wrappers import WrapDocument


class SingleObjectMixin(djmod.SingleObjectMixin, WrapDocument):
    pass


class BaseDetailView(SingleObjectMixin, View):
    get = djmod.BaseDetailView.__dict__["get"]


class DetailView(djmod.SingleObjectTemplateResponseMixin, BaseDetailView):
    pass
