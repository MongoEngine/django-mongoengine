from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _

from django_mongoengine.forms.widgets import Dictionary, EmbeddedFieldWidget


class ReferenceField(forms.ModelChoiceField):
    pass

class DocumentMultipleChoiceField(forms.ModelMultipleChoiceField):
    pass


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

        self.max_depth = (max_depth if max_depth and max_depth >= 0 else None)

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

class EmbeddedDocumentField(forms.MultiValueField):
    def __init__(self, form, *args, **kwargs):
        self.form = form()
        # Set the widget and initial data
        kwargs['widget'] = EmbeddedFieldWidget(self.form.fields)
        kwargs['initial'] = [f.initial for f in self.form.fields.values()]
        kwargs['require_all_fields'] = False
        super(EmbeddedDocumentField, self).__init__(fields=tuple([f for f in self.form.fields.values()]), *args, **kwargs)

    def bound_data(self, data, initial):
        return data

    def prepare_value(self, value):
        return value
    def compress(self, data_list):
        data = {}
        if data_list:
            data = dict((f.name, data_list[i]) for i, f in enumerate(self.form))
            f = self.form.__class__(data)
            f.is_valid()
            return f.cleaned_data
        return data

    def clean(self, value):
        return self.to_python(super(EmbeddedDocumentField, self).clean(value))

    def to_python(self, value):
        obj = self.form._meta.model()
        [ obj.__setattr__(k, value[k]) for k in value.keys() ]
        return obj
