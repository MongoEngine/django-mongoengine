import os
import itertools
import gridfs
import datetime

from django.utils.datastructures import SortedDict

from django.forms.forms import BaseForm, get_declared_fields, NON_FIELD_ERRORS, pretty_name
from django.forms.widgets import media_property
from django.core.exceptions import FieldError
from django.core.validators import EMPTY_VALUES
from django.forms.utils import ErrorList
from django.forms.formsets import BaseFormSet, formset_factory
from django.utils.translation import ugettext_lazy as _
from django.utils.text import capfirst

from mongoengine.fields import ObjectIdField, ListField, ReferenceField, FileField, ImageField
from mongoengine.base import ValidationError
from mongoengine.connection import _get_db

from .field_generator import MongoFormFieldGenerator
from .document_options import DocumentMetaWrapper


def _get_unique_filename(name):
    fs = gridfs.GridFS(_get_db())
    file_root, file_ext = os.path.splitext(name)
    count = itertools.count(1)
    while fs.exists(filename=name):
        # file_ext includes the dot.
        name = os.path.join("%s_%s%s" % (file_root, count.next(), file_ext))
    return name


def construct_instance(form, instance, fields=None, exclude=None, ignore=None):
    """
    Constructs and returns a document instance from the bound ``form``'s
    ``cleaned_data``, but does not save the returned instance to the
    database.
    """
    cleaned_data = form.cleaned_data
    file_field_list = []

    # check wether object is instantiated
    if isinstance(instance, type):
        instance = instance()

    for f in instance._fields.itervalues():
        if isinstance(f, ObjectIdField):
            continue
        if not f.name in cleaned_data:
            continue
        if fields is not None and f.name not in fields:
            continue
        if exclude and f.name in exclude:
            continue
        if f.primary_key and cleaned_data[f.name] == getattr(instance, f.name):
            continue

        # Defer saving file-type fields until after the other fields, so a
        # callable upload_to can use the values from other fields.
        if isinstance(f, FileField) or isinstance(f, ImageField):
            file_field_list.append(f)
        else:
            setattr(instance, f.name, cleaned_data[f.name])

    for f in file_field_list:
        upload = cleaned_data[f.name]
        if upload is None:
            continue
        field = getattr(instance, f.name)
        try:
            upload.file.seek(0)
            filename = _get_unique_filename(upload.name)
            field.replace(upload, content_type=upload.content_type, filename=filename)
            setattr(instance, f.name, field)
        except AttributeError:
            # file was already uploaded and not changed during edit.
            # upload is already the gridfsproxy object we need.
            upload.get()
            setattr(instance, f.name, upload)

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
            new_fields = dict([(n, f) for n, f in fields.iteritems()
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


def document_to_dict(instance, fields=None, exclude=None):
    """
    Returns a dict containing the data in ``instance`` suitable for passing as
    a Form's ``initial`` keyword argument.

    ``fields`` is an optional list of field names. If provided, only the named
    fields will be included in the returned dict.

    ``exclude`` is an optional list of field names. If provided, the named
    fields will be excluded from the returned dict, even if they are listed in
    the ``fields`` argument.
    """
    data = {}
    for f in instance._fields.itervalues():
        if fields and not f.name in fields:
            continue
        if exclude and f.name in exclude:
            continue
        else:
            data[f.name] = getattr(instance, f.name)
    return data


def fields_for_document(document, fields=None, exclude=None, widgets=None,
                        formfield_callback=None,
                        field_generator=MongoFormFieldGenerator):
    """
    Returns a ``SortedDict`` containing form fields for the given model.

    ``fields`` is an optional list of field names. If provided, only the named
    fields will be included in the returned fields.

    ``exclude`` is an optional list of field names. If provided, the named
    fields will be excluded from the returned fields, even if they are listed
    in the ``fields`` argument.
    """
    field_list = []
    ignored = []
    if isinstance(field_generator, type):
        field_generator = field_generator()

    sorted_fields = sorted(document._fields.values(),
                           key=lambda field: field.creation_counter)

    for f in sorted_fields:
        if isinstance(f, ObjectIdField):
            continue
        if isinstance(f, ListField) and not (f.field.choices or isinstance(f.field, ReferenceField)):
            continue
        if fields is not None and not f.name in fields:
            continue
        if exclude and f.name in exclude:
            continue
        if widgets and f.name in widgets:
            kwargs = {'widget': widgets[f.name]}
        else:
            kwargs = {}

        if formfield_callback is None:
            form_field = field_generator.generate(f, **kwargs)
        elif not callable(formfield_callback):
            raise TypeError('formfield_callback must be a function or callable')
        else:
            form_field = formfield_callback(f, **kwargs)

        if form_field:
            field_list.append((f.name, form_field))
        else:
            ignored.append(f.name)

    field_dict = SortedDict(field_list)
    if fields:
        field_dict = SortedDict(
            [(f, field_dict.get(f)) for f in fields
                if ((not exclude) or (exclude and f not in exclude)) and (f not in ignored)]
        )
    return field_dict


class DocumentFormOptions(object):
    def __init__(self, options=None):
        self.document = getattr(options, 'document', None)
        self.model = self.document
        # set up the document meta wrapper if document meta is a dict
        if self.document is not None:
            if not hasattr(self.document, '_meta'):
                self.document._meta = {}
            if isinstance(self.document._meta, dict):
                self.document._meta = DocumentMetaWrapper(self.document)
                self.document._admin_opts = self.document._meta
        self.fields = getattr(options, 'fields', None)
        self.exclude = getattr(options, 'exclude', None)
        self.widgets = getattr(options, 'widgets', None)
        self.embedded_field = getattr(options, 'embedded_field_name', None)
        self.formfield_generator = getattr(options, 'formfield_generator', MongoFormFieldGenerator)


class DocumentFormMetaclass(type):
    def __new__(cls, name, bases, attrs):
        formfield_callback = attrs.pop('formfield_callback', None)
        try:
            parents = [b for b in bases if issubclass(b, DocumentForm) or issubclass(b, EmbeddedDocumentForm)]
        except NameError:
            # We are defining DocumentForm itself.
            parents = None
        declared_fields = get_declared_fields(bases, attrs, False)
        new_class = super(DocumentFormMetaclass, cls).__new__(cls, name, bases, attrs)
        if not parents:
            return new_class

        if 'media' not in attrs:
            new_class.media = media_property(new_class)

        opts = new_class._meta = DocumentFormOptions(getattr(new_class, 'Meta', None))
        if opts.document:
            formfield_generator = getattr(opts, 'formfield_generator', MongoFormFieldGenerator)

            # If a model is defined, extract form fields from it.
            fields = fields_for_document(opts.document, opts.fields,
                            opts.exclude, opts.widgets, formfield_callback, formfield_generator)
            # make sure opts.fields doesn't specify an invalid field
            none_document_fields = [k for k, v in fields.iteritems() if not v]
            missing_fields = set(none_document_fields) - \
                             set(declared_fields.keys())
            if missing_fields:
                message = 'Unknown field(s) (%s) specified for %s'
                message = message % (', '.join(missing_fields),
                                     opts.model.__name__)
                raise FieldError(message)
            # Override default model fields with any custom declared ones
            # (plus, include all the other declared fields).
            fields.update(declared_fields)
        else:
            fields = declared_fields

        new_class.declared_fields = declared_fields
        new_class.base_fields = fields
        return new_class


class BaseDocumentForm(BaseForm):
    def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=':',
                 empty_permitted=False, instance=None):

        opts = self._meta

        if instance is None:
            if opts.document is None:
                raise ValueError('DocumentForm has no document class specified.')
            # if we didn't get an instance, instantiate a new one
            self.instance = opts.document
            object_data = {}
        else:
            self.instance = instance
            object_data = document_to_dict(instance, opts.fields, opts.exclude)

        # if initial was provided, it should override the values from instance
        if initial is not None:
            object_data.update(initial)

        # self._validate_unique will be set to True by BaseModelForm.clean().
        # It is False by default so overriding self.clean() and failing to call
        # super will stop validate_unique from being called.
        self._validate_unique = False
        super(BaseDocumentForm, self).__init__(data, files, auto_id, prefix, object_data,
                                            error_class, label_suffix, empty_permitted)

    def _update_errors(self, message_dict):
        for k, v in message_dict.items():
            if k != NON_FIELD_ERRORS:
                self._errors.setdefault(k, self.error_class()).extend(v)
                # Remove the data from the cleaned_data dict since it was invalid
                if k in self.cleaned_data:
                    del self.cleaned_data[k]
        if NON_FIELD_ERRORS in message_dict:
            messages = message_dict[NON_FIELD_ERRORS]
            self._errors.setdefault(NON_FIELD_ERRORS, self.error_class()).extend(messages)

    def _get_validation_exclusions(self):
        """
        For backwards-compatibility, several types of fields need to be
        excluded from model validation. See the following tickets for
        details: #12507, #12521, #12553
        """
        exclude = []
        # Build up a list of fields that should be excluded from model field
        # validation and unique checks.
        for f in self.instance._fields.itervalues():
            field = f.name
            # Exclude fields that aren't on the form. The developer may be
            # adding these values to the model after form validation.
            if field not in self.fields:
                exclude.append(f.name)

            # Don't perform model validation on fields that were defined
            # manually on the form and excluded via the ModelForm's Meta
            # class. See #12901.
            elif self._meta.fields and field not in self._meta.fields:
                exclude.append(f.name)
            elif self._meta.exclude and field in self._meta.exclude:
                exclude.append(f.name)

            # Exclude fields that failed form validation. There's no need for
            # the model fields to validate them as well.
            elif field in self._errors.keys():
                exclude.append(f.name)

            # Exclude empty fields that are not required by the form, if the
            # underlying model field is required. This keeps the model field
            # from raising a required error. Note: don't exclude the field from
            # validaton if the model field allows blanks. If it does, the blank
            # value may be included in a unique check, so cannot be excluded
            # from validation.
            else:
                field_value = self.cleaned_data.get(field, None)
                if not f.required and field_value in EMPTY_VALUES:
                    exclude.append(f.name)
        return exclude

    def clean(self):
        self._validate_unique = True
        return self.cleaned_data

    def validate_unique(self):
        """
        Validates unique constrains on the document.
        unique_with is not checked at the moment.
        """
        errors = []
        exclude = self._get_validation_exclusions()
        for f in self.instance._fields.itervalues():
            if f.unique and f.name not in exclude:
                filter_kwargs = {
                    f.name: getattr(self.instance, f.name)
                }
                qs = self.instance.__class__.objects().filter(**filter_kwargs)
                # Exclude the current object from the query if we are editing an
                # instance (as opposed to creating a new one)
                if self.instance.pk is not None:
                    qs = qs.filter(pk__ne=self.instance.pk)
                if len(qs) > 0:
                    message = _("%(model_name)s with this %(field_label)s already exists.") % {
                                'model_name': unicode(capfirst(self.instance._meta.verbose_name)),
                                'field_label': unicode(pretty_name(f.name))
                    }
                    err_dict = {f.name: [message]}
                    self._update_errors(err_dict)
                    errors.append(err_dict)

        return errors

    def save(self, commit=True):
        """
        Saves this ``form``'s cleaned_data into model instance
        ``self.instance``.

        If commit=True, then the changes to ``instance`` will be saved to the
        database. Returns ``instance``.
        """

        try:
            if self.instance.pk is None:
                fail_message = 'created'
            else:
                fail_message = 'changed'
        except (KeyError, AttributeError):
            fail_message = 'embedded document saved'

        if self.errors:
            raise ValueError("The %s could not be %s because the data didn't"
                             " validate." % (self.instance.__class__.__name__, fail_message))

        self.instance = construct_instance(self, self.instance, self.fields, self._meta.exclude)

        # Validate uniqueness if needed.
        if self._validate_unique:
            self.validate_unique()

        if commit:
            self.instance.save()

        return self.instance
    save.alters_data = True


class DocumentForm(BaseDocumentForm):
    __metaclass__ = DocumentFormMetaclass


def documentform_factory(document, form=DocumentForm, fields=None,
                         exclude=None, formfield_callback=None):
    # Build up a list of attributes that the Meta object will have.
    attrs = {'document': document, 'model': document}
    if fields is not None:
        attrs['fields'] = fields
    if exclude is not None:
        attrs['exclude'] = exclude

    # If parent form class already has an inner Meta, the Meta we're
    # creating needs to inherit from the parent's inner meta.
    parent = (object,)
    if hasattr(form, 'Meta'):
        parent = (form.Meta, object)
    Meta = type('Meta', parent, attrs)

    # Give this new form class a reasonable name.
    if isinstance(document, type):
        doc_inst = document()
    else:
        doc_inst = document
    class_name = doc_inst.__class__.__name__ + 'Form'

    # Class attributes for the new form class.
    form_class_attrs = {
        'Meta': Meta,
        'formfield_callback': formfield_callback
    }

    return DocumentFormMetaclass(class_name, (form,), form_class_attrs)


class EmbeddedDocumentForm(BaseDocumentForm):
    __metaclass__ = DocumentFormMetaclass

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
                initial.append(document_to_dict(d))
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