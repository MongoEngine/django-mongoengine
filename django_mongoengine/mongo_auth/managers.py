from importlib import import_module

from django.conf import settings
from django.contrib.auth.models import UserManager
from django.db.models import BooleanField, CharField, DateTimeField
from django.utils.translation import gettext_lazy as _
from mongoengine.errors import DoesNotExist

MONGOENGINE_USER_DOCUMENT = getattr(
    settings, 'MONGOENGINE_USER_DOCUMENT', 'django_mongoengine.mongo_auth.models.User'
)


def get_user_document():
    """Get the user document class used for authentication.

    This is the class defined in settings.MONGOENGINE_USER_DOCUMENT, which
    defaults to `mongoengine.django.auth.User`.

    """

    name = MONGOENGINE_USER_DOCUMENT
    dot = name.rindex('.')
    module = import_module(name[:dot])
    return getattr(module, name[dot + 1 :])


class MongoUserManager(UserManager):
    """A User manager wich allows the use of MongoEngine documents in Django.

    To use the manager, you must tell django.contrib.auth to use MongoUser as
    the user model. In you settings.py, you need:

        INSTALLED_APPS = (
            ...
            'django.contrib.auth',
            'django_mongoengine.mongo_auth',
            ...
        )
        AUTH_USER_MODEL = 'mongo_auth.MongoUser'

    Django will use the model object to access the custom Manager, which will
    replace the original queryset with MongoEngine querysets.

    By default, `mongo_auth.User` will be used to store users. You
    can specify another document class in MONGOENGINE_USER_DOCUMENT in your
    settings.py.

    The User Document class has the same requirements as a standard custom user
    model: https://docs.djangoproject.com/en/dev/topics/auth/customizing/

    In particular, the User Document class must define USERNAME_FIELD and
    REQUIRED_FIELDS.
    """

    def contribute_to_class(self, model, name):
        super().contribute_to_class(model, name)
        self.dj_model = self.model
        self.model = get_user_document()

        self.dj_model.USERNAME_FIELD = self.model.USERNAME_FIELD
        username = CharField(_('username'), max_length=30, unique=True)
        username.contribute_to_class(self.dj_model, self.dj_model.USERNAME_FIELD)

        self.dj_model.REQUIRED_FIELDS = self.model.REQUIRED_FIELDS
        for name in self.dj_model.REQUIRED_FIELDS:
            field = CharField(_(name), max_length=30)
            field.contribute_to_class(self.dj_model, name)

        is_staff = BooleanField(_('is_staff'), default=False)
        is_staff.contribute_to_class(self.dj_model, 'is_staff')

        is_active = BooleanField(_('is_active'), default=False)
        is_active.contribute_to_class(self.dj_model, 'is_active')

        is_superuser = BooleanField(_('is_superuser'), default=False)
        is_superuser.contribute_to_class(self.dj_model, 'is_superuser')

        last_login = DateTimeField(_('last_login'), auto_now_add=True)
        last_login.contribute_to_class(self.dj_model, 'last_login')

        date_joined = DateTimeField(_('date_joined'), auto_now_add=True)
        date_joined.contribute_to_class(self.dj_model, 'date_joined')

    def get(self, *args, **kwargs):
        try:
            return self.get_queryset().get(*args, **kwargs)
        except DoesNotExist:
            # ModelBackend expects this exception
            raise self.dj_model.DoesNotExist

    @property
    def db(self):
        raise NotImplementedError

    def get_queryset(self):
        return get_user_document().objects

    def create_superuser(self, username, email, password, **extra_fields):
        """since we use mongo as our database, we don't use
        django's rule to create a superuser, such as 'python manage.py createsuperuser'.
        We use mongo's rule --'python manage.py createmongosuperuser instead.
        """
        return get_user_document().create_superuser(username, password, email)
