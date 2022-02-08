from django.utils.text import capfirst
from django.core.validators import RegexValidator
from django.core.exceptions import ImproperlyConfigured
from django import forms
from django.db.models import Field
from django.utils.functional import cached_property

from mongoengine import fields

from django_mongoengine.forms import fields as formfields
from .internal import INTERNAL_DJANGO_FIELDS_MAP

_field_defaults = (
    ("editable", True),
    ("blank", False),
    ("null", False),
    ("help_text", ""),
    ("auto_created", False),
)


class DjangoField(object):
    get_choices = Field.__dict__["get_choices"]

    def _get_flatchoices(self):
        """Flattened version of choices tuple."""
        if self.choices is None:
            return []
        flat = []
        for choice, value in self.choices:
            if isinstance(value, (list, tuple)):
                flat.extend(value)
            else:
                flat.append((choice, value))
        return flat

    flatchoices = property(_get_flatchoices)

    def __init__(self, *args, **kwargs):
        for k, v in _field_defaults:
            kwargs.setdefault(k, v)
        if "required" in kwargs:
            raise ImproperlyConfigured("`required` option is not supported. Use Django-style `blank` instead.")
        kwargs["required"] = not kwargs["blank"]
        if hasattr(self, "auto_created"):
            kwargs.pop("auto_created")
        self._verbose_name = kwargs.pop("verbose_name", None)

        super(DjangoField, self).__init__(*args, **kwargs)
        self.remote_field = None
        self.is_relation = self.remote_field is not None

    def _get_verbose_name(self):
        return self._verbose_name or self.db_field.replace('_', ' ')

    def _set_verbose_name(self, val):
        self._verbose_name = val

    verbose_name = property(_get_verbose_name, _set_verbose_name)

    def formfield(self, form_class=None, choices_form_class=None, **kwargs):
        """
        Returns a django.forms.Field instance for this database Field.
        """

        defaults = {'required': self.required,
                    'label': capfirst(self.verbose_name),
                    'help_text': self.help_text}
        if self.default:
            if callable(self.default):
                defaults['initial'] = self.default
                defaults['show_hidden_initial'] = True
            else:
                defaults['initial'] = self.default
        if self.choices:
            # Fields with choices get special treatment.
            include_blank = (self.blank or
                             not (self.default or 'initial' in kwargs))
            defaults['choices'] = self.get_choices(include_blank=include_blank)
            defaults['coerce'] = self.to_python
            if self.null:
                defaults['empty_value'] = None
            if choices_form_class is not None:
                form_class = choices_form_class
            else:
                form_class = forms.TypedChoiceField
            # Many of the subclass-specific formfield arguments (min_value,
            # max_value) don't apply for choice fields, so be sure to only pass
            # the values that TypedChoiceField will understand.
            for k in list(kwargs):
                if k not in ('coerce', 'empty_value', 'choices', 'required',
                             'widget', 'label', 'initial', 'help_text',
                             'error_messages', 'show_hidden_initial'):
                    del kwargs[k]
        defaults.update(kwargs)
        if form_class is None:
            form_class = forms.CharField
        return form_class(**defaults)

    def get_internal_type(self):
        return INTERNAL_DJANGO_FIELDS_MAP.get(
            self.__class__.__name__,
            "CharField",
        )

    def save_form_data(self, instance, data):
        setattr(instance, self.name, data)

    def value_from_object(self, obj):
        return getattr(obj, self.name)

    @cached_property
    def attname(self):
        return self.db_field

    def __eq__(self, other):
        # Needed for @total_ordering
        if isinstance(other, fields.BaseField):
            return self.creation_counter == other.creation_counter
        return NotImplemented

    def __lt__(self, other):
        # This is needed because bisect does not take a comparison function.
        if isinstance(other, fields.BaseField):
            return self.creation_counter < other.creation_counter
        return NotImplemented

    def __hash__(self):
        return hash(self.creation_counter)


class StringField(DjangoField):

    def formfield(self, form_class=forms.CharField, choices_form_class=None, **kwargs):

        defaults = {}

        if self.max_length and not self.choices:
            defaults['max_length'] = self.max_length

        if self.max_length is None and not self.choices:
            defaults['widget'] = forms.Textarea

        if self.regex:
            defaults['regex'] = self.regex

        defaults.update(kwargs)
        return super(StringField, self).formfield(form_class, choices_form_class, **defaults)


class EmailField(StringField):

    def __init__(self, *args, **kwargs):
        # max_length=254 to be compliant with RFCs 3696 and 5321
        kwargs['max_length'] = kwargs.get('max_length', 254)
        super(EmailField, self).__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        defaults = {
            'form_class': forms.EmailField,
        }
        defaults.update(kwargs)
        return super(EmailField, self).formfield(**defaults)


class URLField(StringField):

    def formfield(self, **kwargs):
        defaults = {
            'form_class': forms.URLField,
        }
        defaults.update(kwargs)
        return super(URLField, self).formfield(**defaults)


class MinMaxMixin(object):

    def formfield(self, **kwargs):
        defaults = {
            'min_value':  self.min_value,
            'max_value':  self.max_value,
        }
        defaults.update(kwargs)
        return super(MinMaxMixin, self).formfield(**defaults)


class IntField(MinMaxMixin, DjangoField):

    def formfield(self, **kwargs):
        defaults = {
            'form_class': forms.IntegerField,
        }
        defaults.update(kwargs)
        return super(IntField, self).formfield(**defaults)


class FloatField(MinMaxMixin, DjangoField):

    def formfield(self, **kwargs):
        defaults = {
            'form_class': forms.FloatField,
        }
        defaults.update(kwargs)
        return super(FloatField, self).formfield(**defaults)


class DecimalField(MinMaxMixin, DjangoField):

    def formfield(self, **kwargs):
        defaults = {
            'max_digits': self.max_digits,
            'decimal_places': self.precision,
            'form_class': forms.DecimalField,
        }
        defaults.update(kwargs)
        return super(DecimalField, self).formfield(**defaults)

# TODO: test boolean choices; test choices

class BooleanField(DjangoField):

    def __init__(self, *args, **kwargs):
        kwargs['blank'] = True

        super(BooleanField, self).__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        # Unlike most fields, BooleanField figures out include_blank from
        # self.null instead of self.blank.
        if self.choices:
            include_blank = not (self.default or 'initial' in kwargs)
            defaults = {'choices': self.get_choices(include_blank=include_blank)}
        else:
            defaults = {'form_class': forms.BooleanField}
        defaults.update(kwargs)
        return super(BooleanField, self).formfield(**defaults)


class DateTimeField(DjangoField):

    def formfield(self, **kwargs):
        defaults = {'form_class': forms.DateTimeField}
        defaults.update(kwargs)
        return super(DateTimeField, self).formfield(**defaults)


class ReferenceField(DjangoField):

    def formfield(self, **kwargs):
        defaults = {
          'form_class': formfields.ReferenceField,
          'queryset': self.document_type.objects,
        }
        defaults.update(kwargs)
        return super(ReferenceField, self).formfield(**defaults)


# TODO: test field.field.choices?
class ListField(DjangoField):
    def formfield(self, **kwargs):
        if self.field.choices:
            defaults = {
                'choices': self.field.choices,
                'widget': forms.CheckboxSelectMultiple,
                'form_class': forms.MultipleChoiceField,
            }
        elif isinstance(self.field, fields.ReferenceField):
            defaults = {
                'form_class': formfields.DocumentMultipleChoiceField,
                'queryset': self.field.document_type.objects,
            }
        else:
            defaults = {}

        defaults.update(kwargs)
        return super(ListField, self).formfield(**defaults)


class FileField(DjangoField):


    def __init__(self, *args, **kwargs):

        kwargs['max_length'] = kwargs.get('max_length', 100)
        super(FileField, self).__init__(*args, **kwargs)

    def formfield(self, **kwargs):
        defaults = {'form_class': forms.FileField, 'max_length': self.max_length}
        # If a file has been provided previously, then the form doesn't require
        # that a new file is provided this time.
        # The code to mark the form field as not required is used by
        # form_for_instance, but can probably be removed once form_for_instance
        # is gone. ModelForm uses a different method to check for an existing file.
        if 'initial' in kwargs:
            defaults['required'] = False
        defaults.update(kwargs)
        return super(FileField, self).formfield(**defaults)


class ImageField(FileField):

    def formfield(self, **kwargs):
        defaults = {'form_class': forms.ImageField}
        defaults.update(kwargs)
        return super(ImageField, self).formfield(**defaults)


class DictField(DjangoField):

    def formfield(self, **kwargs):
        #remove Mongo reserved words
        validators = [
            RegexValidator(
                regex='^[^$_]',
                message=u'Ensure the keys do not begin with : ["$","_"].', code='invalid_start'
            )
        ]
        defaults = {
            'validators': validators,
            'form_class': formfields.DictField,
        }
        return super(DictField, self).formfield(**defaults)


class EmbeddedDocumentField(DjangoField):

    def formfield(self, **kwargs):
        from django_mongoengine.forms.documents import documentform_factory
        defaults = {
            'label': self.label,
            'help_text': self.help_text,
        }
        form_class = EmbeddedDocumentField
        defaults.update(kwargs)
        form = form_class(documentform_factory(self.document_type), **defaults)
        return form
