from django_mongoengine.admin.options import *
from django_mongoengine.admin.sites import site

from django.conf import settings

if getattr(settings, 'DJANGO_MONGOENGINE_OVERRIDE_ADMIN', False):
    import django.contrib.admin
    # copy already registered model admins
    # without that the already registered models
    # don't show up in the new admin
    site._registry = django.contrib.admin.site._registry

    django.contrib.admin.site = site