default_app_config = "django_mongoengine.mongo_admin.apps.MongoAdminConfig"

from .options import DocumentAdmin
from .sites import site

__all__ = ['DocumentAdmin', 'site']
