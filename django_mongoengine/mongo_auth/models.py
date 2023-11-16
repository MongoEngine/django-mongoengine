from bson.objectid import ObjectId
from django.conf import settings
from django.contrib import auth
from django.contrib.auth.models import (
    AbstractBaseUser,
    _user_get_permissions,
    _user_has_module_perms,
    _user_has_perm,
)
from django.contrib.contenttypes.models import ContentTypeManager
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from mongoengine import ImproperlyConfigured

from django_mongoengine import document, fields
from django_mongoengine.queryset import QuerySetManager

from django.contrib.auth.hashers import check_password, make_password
from .managers import MongoUserManager


def ct_init(self, *args, **kwargs):
    super(QuerySetManager, self).__init__(*args, **kwargs)
    self._cache = {}


ContentTypeManager = type(
    "ContentTypeManager",
    (QuerySetManager,),
    dict(
        ContentTypeManager.__dict__,
        __init__=ct_init,
    ),
)


class BaseUser:
    is_anonymous = AbstractBaseUser.__dict__["is_anonymous"]
    is_authenticated = AbstractBaseUser.__dict__["is_authenticated"]

    @classmethod
    def get_email_field_name(cls):
        try:
            return cls.EMAIL_FIELD
        except AttributeError:
            return "email"


class ContentType(document.Document):
    name = fields.StringField(max_length=100)
    app_label = fields.StringField(max_length=100)
    model = fields.StringField(
        max_length=100, verbose_name=_("python model class name"), unique_with="app_label"
    )
    objects = ContentTypeManager()

    class Meta:
        verbose_name = _("content type")
        verbose_name_plural = _("content types")
        # db_table = 'django_content_type'
        # ordering = ('name',)
        # unique_together = (('app_label', 'model'),)

    def __str__(self):
        return self.name

    def model_class(self):
        "Returns the Python model class for this type of content."
        from django.db import models

        return models.get_model(self.app_label, self.model)

    def get_object_for_this_type(self, **kwargs):
        """
        Returns an object of this type for the keyword arguments given.
        Basically, this is a proxy around this object_type's get_object() model
        method. The ObjectNotExist exception, if thrown, will not be caught,
        so code that calls this method should catch it.
        """
        return self.model_class()._default_manager.using(self._state.db).get(**kwargs)

    def natural_key(self):
        return (self.app_label, self.model)


class SiteProfileNotAvailable(Exception):
    pass


class PermissionManager(QuerySetManager):
    def get_by_natural_key(self, codename, app_label, model):
        return self.get(
            codename=codename, content_type=ContentType.objects.get_by_natural_key(app_label, model)
        )


class Permission(document.Document):
    """The permissions system provides a way to assign permissions to specific
    users and groups of users.

    The permission system is used by the Django admin site, but may also be
    useful in your own code. The Django admin site uses permissions as follows:

        - The "add" permission limits the user's ability to view the "add"
          form and add an object.
        - The "change" permission limits a user's ability to view the change
          list, view the "change" form and change an object.
        - The "delete" permission limits the ability to delete an object.

    Permissions are set globally per type of object, not per specific object
    instance. It is possible to say "Mary may change news stories," but it's
    not currently possible to say "Mary may change news stories, but only the
    ones she created herself" or "Mary may only change news stories that have
    a certain status or publication date."

    Three basic permissions -- add, change and delete -- are automatically
    created for each Django model.
    """

    name = fields.StringField(max_length=50, verbose_name=_("username"))
    content_type = fields.ReferenceField(ContentType)
    codename = fields.StringField(max_length=100, verbose_name=_("codename"))
    # FIXME: don't access field of the other class
    # unique_with=['content_type__app_label', 'content_type__model'])

    objects = PermissionManager()

    class Meta:
        verbose_name = _("permission")
        verbose_name_plural = _("permissions")
        # unique_together = (('content_type', 'codename'),)
        # ordering = ('content_type__app_label', 'content_type__model', 'codename')

    def __str__(self):
        return "%s | %s | %s" % (
            self.content_type.app_label,
            self.content_type,
            self.name,
        )

    def natural_key(self):
        return (self.codename,) + self.content_type.natural_key()

    natural_key.dependencies = ["contenttypes.contenttype"]


class Group(document.Document):
    """Groups are a generic way of categorizing users to apply permissions,
    or some other label, to those users. A user can belong to any number of
    groups.

    A user in a group automatically has all the permissions granted to that
    group. For example, if the group Site editors has the permission
    can_edit_home_page, any user in that group will have that permission.

    Beyond permissions, groups are a convenient way to categorize users to
    apply some label, or extended functionality, to them. For example, you
    could create a group 'Special users', and you could write code that would
    do special things to those users -- such as giving them access to a
    members-only portion of your site, or sending them members-only
    e-mail messages.
    """

    name = fields.StringField(max_length=80, unique=True, verbose_name=_("name"))
    permissions = fields.ListField(fields.ReferenceField(Permission, verbose_name=_("permissions")))

    class Meta:
        verbose_name = _("group")
        verbose_name_plural = _("groups")

    def __str__(self):
        return self.name


class AbstractUser(BaseUser, document.Document):
    """A User document that aims to mirror most of the API specified by Django
    at http://docs.djangoproject.com/en/dev/topics/auth/#users
    """

    username = fields.StringField(
        max_length=150,
        verbose_name=_("username"),
        help_text=_("Required. 150 characters or fewer. Letters, numbers and @/./+/-/_ characters"),
        required=True,
    )

    first_name = fields.StringField(
        max_length=30,
        verbose_name=_("first name"),
    )

    last_name = fields.StringField(max_length=30, verbose_name=_("last name"))
    email = fields.EmailField(verbose_name=_("e-mail address"), required=True)
    password = fields.StringField(
        max_length=128,
        verbose_name=_("password"),
        help_text=_(
            "Use '[algo]$[iterations]$[salt]$[hexdigest]' or use the <a href=\"password/\">change password form</a>."
        ),
        required=True,
    )
    is_staff = fields.BooleanField(
        default=False,
        verbose_name=_("staff status"),
        help_text=_("Designates whether the user can log into this admin site."),
    )
    is_active = fields.BooleanField(
        default=True,
        verbose_name=_("active"),
        help_text=_(
            "Designates whether this user should be treated as active. Unselect this instead of deleting accounts."
        ),
    )
    is_superuser = fields.BooleanField(
        default=False,
        verbose_name=_("superuser status"),
        help_text=_(
            "Designates that this user has all permissions without explicitly assigning them."
        ),
    )
    last_login = fields.DateTimeField(default=timezone.now, verbose_name=_("last login"))
    date_joined = fields.DateTimeField(default=timezone.now, verbose_name=_("date joined"))

    user_permissions = fields.ListField(
        fields.ReferenceField(Permission),
        verbose_name=_("user permissions"),
        help_text=_("Permissions for the user."),
    )

    USERNAME_FIELD = getattr(settings, "MONGOENGINE_USERNAME_FIELDS", "username")
    REQUIRED_FIELDS = getattr(settings, "MONGOENGINE_USER_REQUIRED_FIELDS", ["email"])

    meta = {"abstract": True, "indexes": [{"fields": ["username"], "unique": True, "sparse": True}]}

    def __str__(self):
        return self.username

    def get_full_name(self):
        """Returns the users first and last names, separated by a space."""
        full_name = "%s %s" % (self.first_name or "", self.last_name or "")
        return full_name.strip()

    def set_password(self, raw_password):
        """Sets the user's password - always use this rather than directly
        assigning to :attr:`~mongoengine.django.auth.User.password` as the
        password is hashed before storage.
        """
        self.password = make_password(raw_password)
        self.save()
        return self

    def check_password(self, raw_password):
        """Checks the user's password against a provided password - always use
        this rather than directly comparing to
        :attr:`~mongoengine.django.auth.User.password` as the password is
        hashed before storage.
        """
        return check_password(raw_password, self.password)

    @classmethod
    def _create_user(cls, username, password, email=None, create_superuser=False):
        """Create (and save) a new user with the given username, password and
        email address.
        """
        now = timezone.now()

        # Normalize the address by lowercasing the domain part of the email
        # address.
        if email is not None:
            try:
                email_name, domain_part = email.strip().split("@", 1)
            except ValueError:
                pass
            else:
                email = "@".join([email_name, domain_part.lower()])

        user = cls(username=username, email=email, date_joined=now)
        user.set_password(password)
        if create_superuser:
            user.is_staff = True
            user.is_superuser = True
        user.save()
        return user

    @classmethod
    def create_user(cls, username, password, email=None):
        return cls._create_user(username, password, email)

    @classmethod
    def create_superuser(cls, username, password, email=None):
        return cls._create_user(username, password, email, create_superuser=True)

    def get_group_permissions(self, obj=None):
        """
        Returns a list of permission strings that this user has through his/her
        groups. This method queries all available auth backends. If an object
        is passed in, only permissions matching this object are returned.
        """
        permissions = set()
        for backend in auth.get_backends():
            if hasattr(backend, "get_group_permissions"):
                permissions.update(backend.get_group_permissions(self, obj))
        return permissions

    def get_all_permissions(self, obj=None):
        return _user_get_permissions(self, obj, "all")

    def has_perm(self, perm, obj=None):
        """
        Returns True if the user has the specified permission. This method
        queries all available auth backends, but returns immediately if any
        backend returns True. Thus, a user who has permission from a single
        auth backend is assumed to have permission in general. If an object is
        provided, permissions for this specific object are checked.
        """

        # Active superusers have all permissions.
        if self.is_active and self.is_superuser:
            return True

        # Otherwise we need to check the backends.
        return _user_has_perm(self, perm, obj)

    def has_perms(self, perm_list, obj=None):
        """
        Returns True if the user has each of the specified permissions. If
        object is passed, it checks if the user has all required perms for this
        object.
        """
        for perm in perm_list:
            if not self.has_perm(perm, obj):
                return False
        return True

    def has_module_perms(self, app_label):
        """
        Returns True if the user has any permissions in the given app label.
        Uses pretty much the same logic as has_perm, above.
        """
        # Active superusers have all permissions.
        if self.is_active and self.is_superuser:
            return True

        return _user_has_module_perms(self, app_label)

    def email_user(self, subject, message, from_email=None):
        "Sends an e-mail to this User."
        from django.core.mail import send_mail

        send_mail(subject, message, from_email, [self.email])

    def get_profile(self):
        """
        Returns site-specific profile for this user. Raises
        SiteProfileNotAvailable if this site does not allow profiles.
        """
        if not hasattr(self, "_profile_cache"):
            if not getattr(settings, "AUTH_PROFILE_MODULE", False):
                raise SiteProfileNotAvailable(
                    "You need to set AUTH_PROFILE_MO" "DULE in your project settings"
                )
            try:
                app_label, model_name = settings.AUTH_PROFILE_MODULE.split(".")
            except ValueError:
                raise SiteProfileNotAvailable(
                    "app_label and model_name should"
                    " be separated by a dot in the AUTH_PROFILE_MODULE set"
                    "ting"
                )

            try:
                model = models.get_model(app_label, model_name)
                if model is None:
                    raise SiteProfileNotAvailable(
                        "Unable to load the profile "
                        "model, check AUTH_PROFILE_MODULE in your project sett"
                        "ings"
                    )
                self._profile_cache = model._default_manager.using(self._state.db).get(
                    user__id__exact=self.id
                )
                self._profile_cache.user = self
            except (ImportError, ImproperlyConfigured):
                raise SiteProfileNotAvailable
        return self._profile_cache


class User(AbstractUser):
    meta = {"allow_inheritance": True}


class MongoUser(BaseUser, models.Model):
    """ "
    Dummy user model for Django.

    MongoUser is used to replace Django's UserManager with MongoUserManager.
    The actual user document class is django_mongoengine.auth.models.User or any
    other document class specified in MONGOENGINE_USER_DOCUMENT.

    To get the user document class, use `get_user_document()`.

    """

    objects = MongoUserManager()

    class Meta:
        app_label = "mongo_auth"

    def set_password(self, password):
        """Doesn't do anything, but works around the issue with Django 1.6."""
        make_password(password)


MongoUser._meta.pk.to_python = ObjectId
