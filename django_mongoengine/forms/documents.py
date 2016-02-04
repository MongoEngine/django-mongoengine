from functools import partial

from django.forms.forms import DeclarativeFieldsMetaclass
from django.forms.models import ALL_FIELDS
from django.core.exceptions import FieldError, ImproperlyConfigured
from django.forms.formsets import BaseFormSet, formset_factory
from django.forms import models as model_forms
from django.utils.translation import ugettext_lazy as _
from django.utils import six

from mongoengine.fields import ObjectIdField, FileField
from mongoengine.base import ValidationError

from .document_options import DocumentMetaWrapper


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
            new_fields = dict([(n, f) for n, f in six.iteritems(fields)
                                if not n in form._delete_before_save])
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
        # set up the document meta wrapper if document meta is a dict
        self.model = getattr(options, 'document', None) or getattr(options, 'model', None)
        if self.model is not None:
            if not hasattr(self.model, '_meta'):
                self.model._meta = {}
            if isinstance(self.model._meta, dict):
                self.model._meta = DocumentMetaWrapper(self.model)
            options.model = self.model
        self.embedded_field = getattr(options, 'embedded_field_name', None)


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
            if isinstance(value, six.string_types) and value != ALL_FIELDS:
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

            fields = model_forms.fields_for_model(
                opts.model, opts.fields, opts.exclude,
                opts.widgets, formfield_callback,
                opts.localized_fields, opts.labels,
                opts.help_texts, opts.error_messages,
                opts.field_classes,
            )

            # make sure opts.fields doesn't specify an invalid field
            none_model_fields = [k for k, v in six.iteritems(fields) if not v]
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

        return self.instance
    save.alters_data = True


@six.add_metaclass(DocumentFormMetaclass)
class DocumentForm(BaseDocumentForm):
    pass


documentform_factory = partial(model_forms.modelform_factory, form=DocumentForm)


@six.add_metaclass(DocumentFormMetaclass)
class EmbeddedDocumentForm(BaseDocumentForm):

    def __init__(self, parent_document, *args, **kwargs):
        super(EmbeddedDocumentForm, self).__init__(*args, **kwargs)
        self.parent_document = parent_document
        if self._meta.embedded_field is not None and \
                not hasattr(self.parent_document, self._meta.embedded_field):
            raise FieldError("Parent document must have field %s" % self._meta.embedded_field)

    def save(self, commit=True):
        if self.errors:
            raise ValueError("The %s could not be saved because the data didn't"
                         " validate." % self.instance.__class__.__name__)

        if commit:
            instance = construct_instance(self, self.instance, self.fields, self._meta.exclude)
            l = getattr(self.parent_document, self._meta.embedded_field)
            l.append(instance)
            setattr(self.parent_document, self._meta.embedded_field, l)
            self.parent_document.save()

        return self.instance


class BaseDocumentFormSet(BaseFormSet):
    """
    A ``FormSet`` for editing a queryset and/or adding new objects to it.
    """

    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 queryset=None, **kwargs):
        self.queryset = queryset
        self._queryset = self.queryset
        self.initial = self.construct_initial()
        defaults = {'data': data, 'files': files, 'auto_id': auto_id,
                    'prefix': prefix, 'initial': self.initial}
        defaults.update(kwargs)
        super(BaseDocumentFormSet, self).__init__(**defaults)

    def construct_initial(self):
        initial = []
        try:
            for d in self.get_queryset():
                initial.append(model_forms.model_to_dict(d))
        except TypeError:
            pass
        return initial

    def initial_form_count(self):
        """Returns the number of forms that are required in this FormSet."""
        if not (self.data or self.files):
            return len(self.get_queryset())
        return super(BaseDocumentFormSet, self).initial_form_count()

    def get_queryset(self):
        return self._queryset

    def save_object(self, form):
        obj = form.save(commit=False)
        return obj

    def save(self, commit=True):
        """
        Saves model instances for every form, adding and changing instances
        as necessary, and returns the list of instances.
        """
        saved = []
        for form in self.forms:
            if not form.has_changed() and not form in self.initial_forms:
                continue
            obj = self.save_object(form)

            if form in self.deleted_forms:
                try:
                    obj.delete()
                except AttributeError:
                    # if it has no delete method it is an
                    # embedded object. We just don't add to the list
                    # and it's gone. Cook huh?
                    continue
            saved.append(obj)
        return saved

    def clean(self):
        self.validate_unique()

    def validate_unique(self):
        errors = []
        for form in self.forms:
            if not hasattr(form, 'cleaned_data'):
                continue
            errors += form.validate_unique()

        if errors:
            raise ValidationError(errors)

    def get_date_error_message(self, date_check):
        return _("Please correct the duplicate data for %(field_name)s "
            "which must be unique for the %(lookup)s in %(date_field)s.") % {
            'field_name': date_check[2],
            'date_field': date_check[3],
            'lookup': unicode(date_check[1]),
        }

    def get_form_error(self):
        return _("Please correct the duplicate values below.")


def documentformset_factory(document, form=DocumentForm, formfield_callback=None,
                         formset=BaseDocumentFormSet,
                         extra=1, can_delete=False, can_order=False,
                         max_num=None, fields=None, exclude=None):
    """
    Returns a FormSet class for the given Django model class.
    """
    form = documentform_factory(document, form=form, fields=fields, exclude=exclude,
                             formfield_callback=formfield_callback)
    FormSet = formset_factory(form, formset, extra=extra, max_num=max_num,
                              can_order=can_order, can_delete=can_delete)
    FormSet.model = document
    FormSet.document = document
    return FormSet


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
