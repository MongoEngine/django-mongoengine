from functools import partial

from django.forms.forms import DeclarativeFieldsMetaclass
from django.forms.models import ALL_FIELDS
from django.core.exceptions import FieldError, ImproperlyConfigured
from django.forms import models as model_forms

from mongoengine.fields import ObjectIdField, FileField
from mongoengine.errors import ValidationError


def construct_instance(form, instance, fields=None, exclude=None):
    """
    Constructs and returns a model instance from the bound ``form``'s
    ``cleaned_data``, but does not save the returned instance to the
    database.
    """
    opts = instance._meta

    cleaned_data = form.cleaned_data
    file_field_list = []
    for f in opts.fields:
        try:
            if not f.editable or isinstance(f, ObjectIdField) or f.name not in cleaned_data:
                continue
        except AttributeError:
            # probably this is StringField() added automatically for inherited fields
            # so we ignore it
            continue
        if fields is not None and f.name not in fields:
            continue
        if exclude and f.name in exclude:
            continue
        # Defer saving file-type fields until after the other fields, so a
        # callable upload_to can use the values from other fields.
        if isinstance(f, FileField):
            file_field_list.append(f)
        else:
            f.save_form_data(instance, cleaned_data[f.name])

    for f in file_field_list:
        f.save_form_data(instance, cleaned_data[f.name])

    return instance



def save_instance(form, instance, fields=None, fail_message='saved',
                  commit=True, exclude=None, construct=True):
    """
    Saves bound Form ``form``'s cleaned_data into document instance ``instance``.

    If commit=True, then the changes to ``instance`` will be saved to the
    database. Returns ``instance``.

    If construct=False, assume ``instance`` has already been constructed and
    just needs to be saved.
    """
    instance = construct_instance(form, instance, fields, exclude)
    if form.errors:
        raise ValueError("The %s could not be %s because the data didn't"
                         " validate." % (instance.__class__.__name__,
                                         fail_message))

    if commit and hasattr(instance, 'save'):
        # see BaseDocumentForm._post_clean for an explanation
        if hasattr(form, '_delete_before_save'):
            fields = instance._fields
            new_fields = dict([
                (n, f)
                for n, f in fields.items()
                if n not in form._delete_before_save
            ])
            if hasattr(instance, '_changed_fields'):
                for field in form._delete_before_save:
                    instance._changed_fields.remove(field)
            instance._fields = new_fields
            instance.save()
            instance._fields = fields
        else:
            instance.save()

    return instance



class DocumentFormOptions(model_forms.ModelFormOptions):
    def __init__(self, options=None):
        super(DocumentFormOptions, self).__init__(options)
        self.model = getattr(options, 'document', None) or getattr(options, 'model', None)
        if self.model is not None:
            options.model = self.model
        self.embedded_field = getattr(options, 'embedded_field', None)


class DocumentFormMetaclass(DeclarativeFieldsMetaclass):
    def __new__(mcs, name, bases, attrs):
        formfield_callback = attrs.pop('formfield_callback', None)

        new_class = super(DocumentFormMetaclass, mcs).__new__(mcs, name, bases, attrs)

        if bases == (BaseDocumentForm,):
            return new_class

        opts = new_class._meta = DocumentFormOptions(getattr(new_class, 'Meta', None))

        # We check if a string was passed to `fields` or `exclude`,
        # which is likely to be a mistake where the user typed ('foo') instead
        # of ('foo',)
        for opt in ['fields', 'exclude', 'localized_fields']:
            value = getattr(opts, opt)
            if isinstance(value, str) and value != ALL_FIELDS:
                msg = ("%(model)s.Meta.%(opt)s cannot be a string. "
                       "Did you mean to type: ('%(value)s',)?" % {
                           'model': new_class.__name__,
                           'opt': opt,
                           'value': value,
                       })
                raise TypeError(msg)

        if opts.model:
            # If a model is defined, extract form fields from it.
            if opts.fields is None and opts.exclude is None:
                raise ImproperlyConfigured(
                    "Creating a ModelForm without either the 'fields' attribute "
                    "or the 'exclude' attribute is prohibited; form %s "
                    "needs updating." % name
                )

            if opts.fields == ALL_FIELDS:
                # Sentinel for fields_for_model to indicate "get the list of
                # fields from the model"
                opts.fields = None

            if hasattr(opts, 'field_classes'):
                fields = model_forms.fields_for_model(
                    opts.model, opts.fields, opts.exclude,
                    opts.widgets, formfield_callback,
                    opts.localized_fields, opts.labels,
                    opts.help_texts, opts.error_messages,
                    opts.field_classes,
                ) 
            else:
                fields = model_forms.fields_for_model(
                    opts.model, opts.fields, opts.exclude,
                    opts.widgets, formfield_callback,
                    opts.localized_fields, opts.labels,
                    opts.help_texts, opts.error_messages,
                )

            # make sure opts.fields doesn't specify an invalid field
            none_model_fields = [k for k, v in fields.items() if not v]
            missing_fields = (set(none_model_fields) -
                              set(new_class.declared_fields.keys()))
            if missing_fields:
                message = 'Unknown field(s) (%s) specified for %s'
                message = message % (', '.join(missing_fields),
                                     opts.model.__name__)
                raise FieldError(message)
            # Override default model fields with any custom declared ones
            # (plus, include all the other declared fields).
            fields.update(new_class.declared_fields)
        else:
            fields = new_class.declared_fields

        new_class.base_fields = fields

        return new_class


class BaseDocumentForm(model_forms.BaseModelForm):

    def _save_m2m(self):
        pass

    def _post_clean(self):
        opts = self._meta

        # mongo MetaDict does not have fields attribute
        # adding it here istead of rewriting code
        self.instance._meta.fields = opts.model._meta.fields
        exclude = self._get_validation_exclusions()

        try:
            self.instance = construct_instance(self, self.instance, opts.fields, exclude)
        except ValidationError as e:
            self._update_errors(e)

    def save(self, commit=True):
        """
        Saves this ``form``'s cleaned_data into model instance
        ``self.instance``.

        If commit=True, then the changes to ``instance`` will be saved to the
        database. Returns ``instance``.
        """

        if self.errors:
            try:
                if self.instance.pk is None:
                    fail_message = 'created'
                else:
                    fail_message = 'changed'
            except (KeyError, AttributeError):
                fail_message = 'embedded document saved'
            raise ValueError(
                "The %s could not be %s because the data didn't"
                " validate." % (self.instance.__class__.__name__, fail_message))

        if commit:
            self.instance.save()
        else:
            self.save_m2m = self._save_m2m

        return self.instance
    save.alters_data = True


class DocumentForm(BaseDocumentForm, metaclass=DocumentFormMetaclass):
    pass


def documentform_factory(
    model, form=DocumentForm, fields=None, exclude=None, formfield_callback=None,
    widgets=None, localized_fields=None, labels=None, help_texts=None,
    error_messages=None, *args, **kwargs
):
    return model_forms.modelform_factory(
        model, form, fields, exclude, formfield_callback, widgets, localized_fields,
        labels, help_texts, error_messages, *args, **kwargs
    )


class EmbeddedDocumentForm(BaseDocumentForm, metaclass=DocumentFormMetaclass):

    def __init__(self, parent_document, *args, **kwargs):
        super(EmbeddedDocumentForm, self).__init__(*args, **kwargs)
        self.parent_document = parent_document
        if self._meta.embedded_field is None:
            raise FieldError("%s.Meta must have defined embedded_field" % self.__class__.__name__)
        if not hasattr(self.parent_document, self._meta.embedded_field):
            raise FieldError("Parent document must have field %s" % self._meta.embedded_field)

    def save(self, commit=True):
        if self.errors:
            raise ValueError(
                "The %s could not be saved because the data didn't"
                " validate." % self.instance.__class__.__name__
            )

        def save(*args, **kwargs):
            instance = construct_instance(self, self.instance, self.fields, self._meta.exclude)
            l = getattr(self.parent_document, self._meta.embedded_field)
            l.append(instance)
            setattr(self.parent_document, self._meta.embedded_field, l)
            self.parent_document.save(*args, **kwargs)
        if commit:
            save()
        else:
            self.instance.save = save

        return self.instance


class BaseDocumentFormSet(model_forms.BaseModelFormSet):
    """
    A ``FormSet`` for editing a queryset and/or adding new objects to it.
    """

def documentformset_factory(
    model, form=DocumentForm, formfield_callback=None, formset=BaseDocumentFormSet,
    extra=1, can_delete=False, can_order=False, max_num=None, fields=None,
    exclude=None, widgets=None, validate_max=False, localized_fields=None,
    labels=None, help_texts=None, error_messages=None, min_num=None,
    validate_min=False, *args, **kwargs
):
    return model_forms.modelformset_factory(
        model, form, formfield_callback, formset, extra, can_delete, can_order,
        max_num, fields, exclude, widgets, validate_max, localized_fields, labels,
        help_texts, error_messages, min_num, validate_min, *args, **kwargs
    )


class BaseInlineDocumentFormSet(BaseDocumentFormSet):
    """
    A formset for child objects related to a parent.

    self.instance -> the document containing the inline objects
    """
    def __init__(self, data=None, files=None, instance=None,
                 save_as_new=False, prefix=None, queryset=[], **kwargs):
        self.instance = instance
        self.save_as_new = save_as_new

        super(BaseInlineDocumentFormSet, self).__init__(data, files, prefix=prefix, queryset=queryset, **kwargs)

    def initial_form_count(self):
        if self.save_as_new:
            return 0
        return super(BaseInlineDocumentFormSet, self).initial_form_count()

    #@classmethod
    def get_default_prefix(cls):
        return cls.model.__name__.lower()
    get_default_prefix = classmethod(get_default_prefix)

    def add_fields(self, form, index):
        super(BaseInlineDocumentFormSet, self).add_fields(form, index)

        # Add the generated field to form._meta.fields if it's defined to make
        # sure validation isn't skipped on that field.
        if form._meta.fields:
            if isinstance(form._meta.fields, tuple):
                form._meta.fields = list(form._meta.fields)
            #form._meta.fields.append(self.fk.name)

    def get_unique_error_message(self, unique_check):
        unique_check = [field for field in unique_check if field != self.fk.name]
        return super(BaseInlineDocumentFormSet, self).get_unique_error_message(unique_check)


def inlineformset_factory(document, form=DocumentForm,
                          formset=BaseInlineDocumentFormSet,
                          fields=None, exclude=None,
                          extra=1, can_order=False, can_delete=True, max_num=None,
                          formfield_callback=None):
    """
    Returns an ``InlineFormSet`` for the given kwargs.

    You must provide ``fk_name`` if ``model`` has more than one ``ForeignKey``
    to ``parent_model``.
    """
    kwargs = {
        'form': form,
        'formfield_callback': formfield_callback,
        'formset': formset,
        'extra': extra,
        'can_delete': can_delete,
        'can_order': can_order,
        'fields': fields,
        'exclude': exclude,
        'max_num': max_num,
    }
    FormSet = documentformset_factory(document, **kwargs)
    return FormSet


class EmbeddedDocumentFormSet(BaseInlineDocumentFormSet):
    def __init__(self, parent_document=None, data=None, files=None, instance=None,
                 save_as_new=False, prefix=None, queryset=[], **kwargs):
        self.parent_document = parent_document
        super(EmbeddedDocumentFormSet, self).__init__(data, files, instance, save_as_new, prefix, queryset, **kwargs)

    def _construct_form(self, i, **kwargs):
        defaults = {'parent_document': self.parent_document}
        defaults.update(kwargs)
        form = super(BaseDocumentFormSet, self)._construct_form(i, **defaults)
        return form


def embeddedformset_factory(document, parent_document, form=EmbeddedDocumentForm,
                          formset=EmbeddedDocumentFormSet,
                          fields=None, exclude=None,
                          extra=1, can_order=False, can_delete=True, max_num=None,
                          formfield_callback=None):
    """
    Returns an ``InlineFormSet`` for the given kwargs.

    You must provide ``fk_name`` if ``model`` has more than one ``ForeignKey``
    to ``parent_model``.
    """
    kwargs = {
        'form': form,
        'formfield_callback': formfield_callback,
        'formset': formset,
        'extra': extra,
        'can_delete': can_delete,
        'can_order': can_order,
        'fields': fields,
        'exclude': exclude,
        'max_num': max_num,
    }
    FormSet = inlineformset_factory(document, **kwargs)
    FormSet.parent_document = parent_document
    return FormSet
