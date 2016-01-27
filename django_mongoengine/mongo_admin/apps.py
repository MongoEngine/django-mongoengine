from django.apps import AppConfig
from django.conf import settings

from django_mongoengine.mongo_admin.sites import site

class MongoAdminConfig(AppConfig):
    name = "django_mongoengine.mongo_admin"
    verbose_name = "Mongo Admin"

    def ready(self):
        if getattr(settings, 'DJANGO_MONGOENGINE_OVERRIDE_ADMIN', False):
            import django.contrib.admin
            # copy already registered model admins
            # without that the already registered models
            # don't show up in the new admin
            site._registry = django.contrib.admin.site._registry

            django.contrib.admin.site = site
