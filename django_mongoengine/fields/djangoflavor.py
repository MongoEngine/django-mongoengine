from django.utils.text import capfirst
from django.core.validators import RegexValidator
from django import forms

from mongoengine import fields

from django_mongoengine.forms import fields as formfields
from django_mongoengine.forms.field_generator import MongoFormFieldGenerator

class DjangoField(object):

    def __init__(self, *args, **kwargs):
        self.editable = kwargs.pop("editable", True)
        self.blank    = kwargs.get("null", False)
        self.verbose_name = kwargs.pop("verbose_name", None)
        self.help_text = kwargs.pop("help_text", None)
        super(DjangoField, self).__init__(*args, **kwargs)
        if self.verbose_name is None and self.name:
            self.verbose_name = self.name.replace('_', ' ')


    def oldformfield(self, **kwargs):
        return MongoFormFieldGenerator().generate(
            self, **kwargs
        )

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


    def save_form_data(self, instance, data):
        setattr(instance, self.name, data)

    def value_from_object(self, obj):
        return getattr(obj, self.name)

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


class StringField(DjangoField):

    def formfield(self, form_class=formfields.MongoCharField, choices_form_class=None, **kwargs):

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

# TODO: check max/min values
class IntField(DjangoField):

    def formfield(self, **kwargs):
        defaults = {
            'form_class': forms.IntegerField,
        }
        defaults.update(kwargs)
        return super(IntField, self).formfield(**defaults)


class FloatField(DjangoField):

    def formfield(self, **kwargs):
        defaults = {
            'form_class': forms.FloatField,
        }
        defaults.update(kwargs)
        return super(FloatField, self).formfield(**defaults)


class DecimalField(DjangoField):

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
        defaults = {'form_class': formfields.ReferenceField}
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
            return None
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
