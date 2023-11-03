from django.contrib.admin import sites
from mongoengine.base import TopLevelDocumentMetaclass

from django_mongoengine.forms.document_options import DocumentMetaWrapper
from django_mongoengine.mongo_admin.options import DocumentAdmin

# from django_mongoengine.mongo_admin import actions

system_check_errors = []


class AdminSite(sites.AdminSite):
    index_template = "mongo_admin/index.html"

    def register(self, model_or_iterable, admin_class=None, **options):
        if isinstance(model_or_iterable, TopLevelDocumentMetaclass) and not admin_class:
            admin_class = DocumentAdmin

        if isinstance(model_or_iterable, TopLevelDocumentMetaclass):
            model_or_iterable._meta = DocumentMetaWrapper(model_or_iterable)
            model_or_iterable = [model_or_iterable]

        super().register(model_or_iterable, admin_class, **options)

    def unregister(self, model_or_iterable):
        if isinstance(model_or_iterable, TopLevelDocumentMetaclass):
            model_or_iterable = [model_or_iterable]

        super().unregister(model_or_iterable)


# This global object represents the default admin site, for the common case.
# You can instantiate AdminSite in your own code to create a custom admin site.
site = AdminSite(name="mongo_admin")
