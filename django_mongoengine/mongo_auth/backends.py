from django.contrib import auth


class MongoEngineBackend(object):
    """Authenticate using MongoEngine and mongoengine.django.auth.User.
    """

    supports_object_permissions = False
    supports_anonymous_user = False
    supports_inactive_user = False

    authenticate = auth.backends.ModelBackend.__dict__["authenticate"]
    get_user = auth.backends.ModelBackend.__dict__["get_user"]
    user_can_authenticate = auth.backends.ModelBackend.__dict__["user_can_authenticate"]
