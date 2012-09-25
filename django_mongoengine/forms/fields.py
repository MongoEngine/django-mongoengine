from django import forms
from django.core.validators import EMPTY_VALUES
from django.core.exceptions import ValidationError
from django.utils.encoding import smart_unicode, force_unicode
from django.utils.translation import ugettext_lazy as _

from django_mongoengine.forms.widgets import Dictionary

from bson.objectid import ObjectId
from bson.errors import InvalidId


class MongoChoiceIterator(object):
    def __init__(self, field):
        self.field = field
        self.queryset = field.queryset

    def __iter__(self):
        if self.field.empty_label is not None:
            yield (u"", self.field.empty_label)

        for obj in self.queryset.all():
            yield self.choice(obj)

    def __len__(self):
        return len(self.queryset)

    def choice(self, obj):
        return (self.field.prepare_value(obj), self.field.label_from_instance(obj))


class MongoCharField(forms.CharField):
    def to_python(self, value):
        if value in EMPTY_VALUES:
            return None
        return smart_unicode(value)


class ReferenceField(forms.ChoiceField):
    """
    Reference field for mongo forms. Inspired by `django.forms.models.ModelChoiceField`.
    """
    def __init__(self, queryset, empty_label=u"---------",
                 *aargs, **kwaargs):

        forms.Field.__init__(self, *aargs, **kwaargs)
        self.queryset = queryset
        self.empty_label = empty_label

    def _get_queryset(self):
        return self._queryset

    def _set_queryset(self, queryset):
        self._queryset = queryset
        self.widget.choices = self.choices

    queryset = property(_get_queryset, _set_queryset)

    def prepare_value(self, value):
        if hasattr(value, '_meta'):
            return value.pk

        return super(ReferenceField, self).prepare_value(value)

    def _get_choices(self):
        return MongoChoiceIterator(self)

    choices = property(_get_choices, forms.ChoiceField._set_choices)

    def label_from_instance(self, obj):
        """
        This method is used to convert objects into strings; it's used to
        generate the labels for the choices presented by this object. Subclasses
        can override this method to customize the display of the choices.
        """
        return smart_unicode(obj)

    def clean(self, value):
        if value in EMPTY_VALUES and not self.required:
            return None

        try:
            oid = ObjectId(value)
            oid = super(ReferenceField, self).clean(oid)

            queryset = self.queryset.clone()
            obj = queryset.get(id=oid)
        except (TypeError, InvalidId, self.queryset._document.DoesNotExist):
            raise forms.ValidationError(self.error_messages['invalid_choice'] % {'value': value})
        return obj

    # Fix for Django 1.4
    # TODO: Test with older django versions
    # from django-mongotools by wpjunior
    # https://github.com/wpjunior/django-mongotools/
    def __deepcopy__(self, memo):
        result = super(forms.ChoiceField, self).__deepcopy__(memo)
        result.queryset = result.queryset
        result.empty_label = result.empty_label
        return result


class DocumentMultipleChoiceField(ReferenceField):
    """A MultipleChoiceField whose choices are a model QuerySet."""
    widget = forms.SelectMultiple
    hidden_widget = forms.MultipleHiddenInput
    default_error_messages = {
        'list': _(u'Enter a list of values.'),
        'invalid_choice': _(u'Select a valid choice. %s is not one of the'
                            u' available choices.'),
        'invalid_pk_value': _(u'"%s" is not a valid value for a primary key.')
    }

    def __init__(self, queryset, *args, **kwargs):
        super(DocumentMultipleChoiceField, self).__init__(queryset, empty_label=None, *args, **kwargs)

    def clean(self, value):
        if self.required and not value:
            raise forms.ValidationError(self.error_messages['required'])
        elif not self.required and not value:
            return []
        if not isinstance(value, (list, tuple)):
            raise forms.ValidationError(self.error_messages['list'])
        key = 'pk'

        filter_ids = []
        for pk in value:
            try:
                oid = ObjectId(pk)
                filter_ids.append(oid)
            except InvalidId:
                raise forms.ValidationError(self.error_messages['invalid_pk_value'] % pk)
        qs = self.queryset.clone()
        qs = qs.filter(**{'%s__in' % key: filter_ids})
        pks = set([force_unicode(getattr(o, key)) for o in qs])
        for val in value:
            if force_unicode(val) not in pks:
                raise forms.ValidationError(self.error_messages['invalid_choice'] % val)
        # Since this overrides the inherited ModelChoiceField.clean
        # we run custom validators here
        self.run_validators(value)
        return list(qs)

    def prepare_value(self, value):
        if hasattr(value, '__iter__') and not hasattr(value, '_meta'):
            return [super(DocumentMultipleChoiceField, self).prepare_value(v) for v in value]
        return super(DocumentMultipleChoiceField, self).prepare_value(value)


class DictField(forms.Field):
    """
    DictField for mongo forms
    """

    error_messages = {
        'length': _(u'Ensure the keys length is less than or equal to %s.'),
        'invalid_key': _(u'Ensure the keys are not : %s.'),
        'illegal': _(u'Ensure the keys does not contain any illegal character : %s.'),
        'depth': _(u'Ensure the dictionary depth is less than or equal to %s.')
    }

    #Mongo reserved keywords
    invalid_keys = ['err', 'errmsg']
    #Mongo prohibit . in keys
    illegal_characters = ['.']
    #limit key length for efficiency
    key_limit = 200
    #limit depth for dictionaries
    max_depth = None

    def __init__(self, max_depth=None, flags=None, sub_attrs=None, attrs=None, *args, **kwargs):
        if 'error_messages' in kwargs.keys():
            kwargs['error_messages'].update(self.error_messages)
        else:
            kwargs['error_messages'] = self.error_messages

        self.max_depth = (max_depth if max_depth >= 0 else None)

        if 'widget' not in kwargs.keys():
            schema = None
            #Here it needs to be clearer, because this is only useful when creating an object,
            #if no default value is provided, default is callable
            if 'initial' in kwargs and not callable(kwargs['initial']):
                if isinstance(kwargs['initial'], dict):
                    schema = kwargs['initial']

            #here if other parameters are passed, like max_depth and flags, then we hand them to the dict
            kwargs['widget'] = Dictionary(max_depth=max_depth, flags=flags, schema=schema, sub_attrs=sub_attrs)

        super(DictField, self).__init__(*args, **kwargs)

    def prepare_value(self, value):
        return value

    def to_python(self, value):
        value = self.get_dict(value)
        return value

    def clean(self, value):
        self.max_depth = self.widget.max_depth
        value = self.to_python(value)
        self.validate(value)
        return value

    def get_dict(self, a_list):
        """
        A function that return a dictionary from a list of lists, with any depth
        """
        d = {}
        for k in a_list:
            if (isinstance(k, list)):
                if isinstance(k[1], list) and k[0]:
                    d.update({k[0]: self.get_dict(k[1])})
                elif k[0]:
                    d.update({k[0]: k[1]})
        return d

    def validate(self, value, depth=0):
        #we should not use the super.validate method
        if self.max_depth is not None and depth > self.max_depth:
            raise ValidationError(self.error_messages['depth'] % self.max_depth)
        for k, v in value.items():
            self.run_validators(k)
            if k in self.invalid_keys:
                raise ValidationError(self.error_messages['invalid_key'] % self.invalid_keys)
            if len(k) > self.key_limit:
                raise ValidationError(self.error_messages['length'] % self.key_limit)
            for u in self.illegal_characters:
                if u in k:
                    raise ValidationError(self.error_messages['illegal'] % self.illegal_characters)
            if isinstance(v, dict):
                self.validate(v, depth + 1)
