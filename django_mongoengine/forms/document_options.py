import sys
import warnings

from django.core.exceptions import FieldDoesNotExist
from django.utils.text import capfirst
from django.utils.encoding import smart_str
from django.db.models.options import Options

try:
    from django.db.models.options import get_verbose_name as camel_case_to_spaces
except ImportError:
    from django.utils.text import camel_case_to_spaces, format_lazy


from mongoengine.fields import ReferenceField


class PkWrapper(object):
    """Used to wrap the Primary Key so it can mimic Django's expectations
    """
    editable = False
    remote_field = None

    def __init__(self, wrapped):
        self.obj = wrapped

    def __getattr__(self, attr):
        if attr in dir(self.obj):
            return getattr(self.obj, attr)
        raise AttributeError("{} has no {}".format(self, attr))

    def __setattr__(self, attr, value):
        if attr != 'obj' and hasattr(self.obj, attr):
            setattr(self.obj, attr, value)
        super(PkWrapper, self).__setattr__(attr, value)

    def value_to_string(self, obj):
        """
        Returns a string value of this field from the passed obj.
        This is used by the serialization framework.
        """
        return smart_str(obj.pk)

    def get_internal_type(self):
        return "CharField"


class DocumentMetaWrapper(object):
    """
    Used to store mongoengine's _meta dict to make the document admin
    as compatible as possible to django's meta class on models.
    """
    _pk = None
    pk_name = None
    app_label = None
    model_name = None
    verbose_name = None
    has_auto_field = False
    abstract = False
    object_name = None
    proxy = []
    virtual_fields = []
    concrete_fields = []
    proxied_children = []
    parents = {}
    private_fields = []
    many_to_many = []
    related_fkey_lookups = []
    swapped = False
    _field_cache = None
    document = None
    _meta = None
    try:
        default_apps = Options.default_apps
    except AttributeError:
        pass
    app_config = Options.__dict__["app_config"]
    try:
        _property_names = Options.__dict__["_property_names"]
    except KeyError:
        pass

    def __init__(self, document):
        if isinstance(document._meta, DocumentMetaWrapper):
            meta = document._meta._meta
        else:
            meta = document._meta
        self.document = document
        self._meta = meta or {}
        self.model = document
        self.concrete_model = document
        self.concrete_fields = document._fields.values()
        self.fields = self.concrete_fields
        try:
            self.apps = self.default_apps
        except AttributeError:
            pass
        try:
            self.object_name = self.document.__name__
        except AttributeError:
            self.object_name = self.document.__class__.__name__

        self.model_name = self.object_name.lower()
        self.app_label = self.get_app_label()
        self.verbose_name = self.get_verbose_name()

        # EmbeddedDocuments don't have an id field.
        try:
            self.pk_name = self._meta['id_field']
            self._init_pk()
        except KeyError:
            pass

    @property
    def module_name(self):
        """
        This property has been deprecated in favor of `model_name`.
        """
        warnings.warn(
            "Options.module_name has been deprecated in favor of model_name",
            PendingDeprecationWarning, stacklevel=2)
        return self.model_name

    def get_app_label(self):
        if 'app_label' in self._meta:
            return self._meta['app_label']
        else:
            model_module = sys.modules[self.document.__module__]
            return model_module.__name__.split('.')[-2]

    def get_verbose_name(self):
        """
        Returns the verbose name of the document.

        Checks the original meta dict first. If it is not found
        then generates a verbose name from from the object name.
        """
        if 'verbose_name' in self._meta:
            return self._meta['verbose_name']
        else:
            return capfirst(camel_case_to_spaces(self.object_name))

    @property
    def verbose_name_raw(self):
        return str(self.verbose_name)

    @property
    def verbose_name_plural(self):
        if 'verbose_name_plural' in self._meta:
            return self.meta['verbose_name_plural']
        else:
            return format_lazy("{}s", self.verbose_name)

    @property
    def pk(self):
        if not hasattr(self._pk, 'attname'):
            self._init_pk()
        return self._pk

    def get_fields(self, include_parents=True, include_hidden=False):
        # XXX: simple placeholder; TODO: handle options;
        return self.concrete_fields

    def _init_pk(self):
        """
        Adds a wrapper around the documents pk field. The wrapper object gets the attributes
        django expects on the pk field, like name and attname.

        The function also adds a _get_pk_val method to the document.
        """
        if self.id_field is None:
            return

        try:
            pk_field = getattr(self.document, self.id_field)
            self._pk = PkWrapper(pk_field)
            self._pk.name = self.id_field
            self._pk.attname = self.id_field
        except AttributeError:
            return

    def get_add_permission(self):
        return 'add_%s' % self.object_name.lower()

    def get_change_permission(self):
        return 'change_%s' % self.object_name.lower()

    def get_delete_permission(self):
        return 'delete_%s' % self.object_name.lower()

    def get_ordered_objects(self):
        return []

    def get_field_by_name(self, name):
        """
        Returns the (field_object, model, direct, m2m), where field_object is
        the Field instance for the given name, model is the model containing
        this field (None for local fields), direct is True if the field exists
        on this model, and m2m is True for many-to-many relations. When
        'direct' is False, 'field_object' is the corresponding RelatedObject
        for this field (since the field doesn't have an instance associated
        with it).

        Uses a cache internally, so after the first access, this is very fast.
        """
        try:
            try:
                return self._field_cache[name]
            except TypeError:
                self._init_field_cache()
                return self._field_cache[name]
        except KeyError:
            raise FieldDoesNotExist('%s has no field named %r'
                                    % (self.object_name, name))

    def _init_field_cache(self):
        if self._field_cache is None:
            self._field_cache = {}

        for f in self.document._fields.values():
            if isinstance(f, ReferenceField):
                document = f.document_type
                self._field_cache[document._meta.module_name] = (f, document, False, False)
            else:
                self._field_cache[f.name] = (f, None, True, False)

        return self._field_cache

    def get_field(self, name, many_to_many=True):
        """
        Returns the requested field by name. Raises FieldDoesNotExist on error.
        """
        return self.get_field_by_name(name)[0]

    def __getattr__(self, name):
        try:
            return self._meta[name]
        except KeyError as e:
            raise AttributeError(*e.args)

    def __setattr__(self, name, value):
        if not hasattr(self, name):
            self._meta[name] = value
        else:
            super(DocumentMetaWrapper, self).__setattr__(name, value)

    def __getitem__(self, key):
        return self._meta[key]

    def __setitem__(self, key, value):
        self._meta[key] = value

    def __contains__(self, key):
        return key in self._meta

    def get(self, key, default=None):
        try:
            return self.__getitem__(key)
        except KeyError:
            return default

    def get_parent_list(self):
        return []

    def get_all_related_objects(self, *args, **kwargs):
        return []

    def iteritems(self):
        return self._meta.iteritems()

    def items(self):
        return self._meta.items()
