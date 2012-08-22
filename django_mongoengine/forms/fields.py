from django import forms
from django.core.validators import EMPTY_VALUES
from django.utils.encoding import smart_unicode, force_unicode
from django.utils.translation import ugettext_lazy as _

from django_mongoengine.forms.widgets import Dictionary

from bson.objectid import ObjectId
from bson.errors import InvalidId
import pdb

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
            raise forms.ValidationError(self.error_messages['invalid_choice'] % {'value':value})
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

#TODO define a DictField
class DictField(forms.Field):
    """
    DictField for mongo forms
    """

    #TODO : how to add another row to a Dict ?

    def __init__(self, *args, **kwargs):
        super(DictField,self).__init__(*args, **kwargs)
        keys = []
        #pdb.set_trace()
        #if no default value is provided, default is callable
        if not callable(self.initial):
            if isinstance(self.initial,dict):
                keys = self.initial.keys()
        self.widget = Dictionary(keys=keys, min_length=3)

    def prepare_value(self,value):
        return value

    def to_python(self,value):
        #pdb.set_trace()
        #here we do it with initial ; if initial provided, several cases : nothing, only keys or keys+value pairing
        value = dict(value)
        value.pop("",True)
        return value

    def clean(self, value):
        #pdb.set_trace()
        value = self.to_python(value)
        #self.validate(value)
        #self.run_validators(value)
        return value
