from django.apps import AppConfig
from django.core import checks
from django.utils.translation import gettext_lazy as _


def check_admin_app(**kwargs):
    from .sites import system_check_errors

    return system_check_errors


class SimpleMongoAdminConfig(AppConfig):
    """Simple AppConfig which does not do automatic discovery."""

    name = "django_mongoengine.mongo_admin"
    verbose_name = _("Administration")

    def ready(self):
        checks.register(check_admin_app, checks.Tags.admin)


class MongoAdminConfig(SimpleMongoAdminConfig):
    def ready(self):
        super().ready()
        self.module.autodiscover()
