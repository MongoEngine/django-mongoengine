from django.utils.module_loading import autodiscover_modules

from .decorators import register
from .options import DocumentAdmin
from .sites import site

__all__ = ["DocumentAdmin", "site", "register"]


def autodiscover():
    autodiscover_modules("admin", register_to=site)


default_app_config = "django_mongoengine.mongo_admin.apps.MongoAdminConfig"
