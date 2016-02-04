from functools import update_wrapper
from collections import OrderedDict

from django import forms, template
from django.forms.formsets import all_valid
from django.forms.models import modelformset_factory
from django.contrib.admin import widgets, helpers
from django.contrib.admin.utils import unquote, flatten_fieldsets, model_format_dict
from django.contrib.admin.options import BaseModelAdmin, ModelAdmin
from django.contrib import messages
from django.utils import six
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.db import models#, router
try:
    from django.db.models.related import RelatedObject
except ImportError:
    from django.db.models.fields.related import ForeignObjectRel as RelatedObject # noqa
from django.db.models.fields import BLANK_CHOICE_DASH
from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render_to_response
from django.utils.decorators import method_decorator
from django.utils.html import escape, escapejs
from django.utils.safestring import mark_safe
from django.utils.functional import curry
from django.utils.text import capfirst, get_text_list
from django.utils.translation import ugettext as _
from django.utils.translation import ungettext
from django.forms.forms import pretty_name

from django_mongoengine.utils import force_text
from django_mongoengine.fields import (ListField, EmbeddedDocumentField,
                                       ReferenceField, StringField)

from django_mongoengine.mongo_admin import helpers as mongodb_helpers
from django_mongoengine.mongo_admin.util import RelationWrapper
from django_mongoengine.mongo_admin.helpers import AdminForm

from django_mongoengine.utils.wrappers import copy_class
from django_mongoengine.forms.documents import (
    documentform_factory, DocumentForm,
    inlineformset_factory, BaseInlineDocumentFormSet)
from django_mongoengine.forms import save_instance

HORIZONTAL, VERTICAL = 1, 2
# returns the <ul> class for a given radio_admin field
get_ul_class = lambda x: 'radiolist%s' % (
    (x == HORIZONTAL) and ' inline' or ''
)


class IncorrectLookupParameters(Exception):
    pass



csrf_protect_m = method_decorator(csrf_protect)


def formfield(field, form_class=None, **kwargs):
    """
    Returns a django.forms.Field instance for this database Field.
    """
    defaults = {'required': field.required, 'label': pretty_name(field.name)}
    if field.default is not None:
        if callable(field.default):
            defaults['initial'] = field.default()
            defaults['show_hidden_initial'] = True
        else:
            defaults['initial'] = field.default

    if hasattr(field, 'max_length') and field.choices is None:
        defaults['max_length'] = field.max_length

    if field.choices is not None:
        # Many of the subclass-specific formfield arguments (min_value,
        # max_value) don't apply for choice fields, so be sure to only pass
        # the values that TypedChoiceField will understand.
        for k in kwargs.keys():
            if k not in ('coerce', 'empty_value', 'choices', 'required',
                         'widget', 'label', 'initial', 'help_text',
                         'error_messages', 'show_hidden_initial'):
                del kwargs[k]

    defaults.update(kwargs)

    if form_class is not None:
        return form_class(**defaults)
    else:
        from django_mongoengine.forms.field_generator import MongoDefaultFormFieldGenerator
        return MongoDefaultFormFieldGenerator().generate(field, **defaults)


class BaseDocumentAdmin(BaseModelAdmin):
    """Functionality common to both ModelAdmin and InlineAdmin."""
    form = DocumentForm

    def formfield_for_dbfield(self, db_field, **kwargs):
        """
        Hook for specifying the form Field instance for a given database Field
        instance.

        If kwargs are given, they're passed to the form Field's constructor.
        """
        request = kwargs.pop("request", None)

        # If the field specifies choices, we don't need to look for special
        # admin widgets - we just need to use a select widget of some kind.
        if db_field.choices is not None:
            return self.formfield_for_choice_field(db_field, request, **kwargs)

        if isinstance(db_field, ListField) and isinstance(db_field.field, ReferenceField):
            return self.formfield_for_manytomany(db_field, request, **kwargs)

        # handle RelatedFields
        if isinstance(db_field, ReferenceField):
            # For non-raw_id fields, wrap the widget with a wrapper that adds
            # extra HTML -- the "add other" interface -- to the end of the
            # rendered output. formfield can be None if it came from a
            # OneToOneField with parent_link=True or a M2M intermediary.
            form_field = formfield(db_field, **kwargs)
            if db_field.name not in self.raw_id_fields:
                related_modeladmin = self.admin_site._registry.get(db_field.document_type)
                can_add_related = bool(related_modeladmin and
                            related_modeladmin.has_add_permission(request))
                form_field.widget = widgets.RelatedFieldWidgetWrapper(
                            form_field.widget, RelationWrapper(db_field.document_type), self.admin_site,
                            can_add_related=can_add_related)
                return form_field

        if isinstance(db_field, StringField):
            if db_field.max_length is None:
                kwargs = dict({'widget': widgets.AdminTextareaWidget}, **kwargs)
            else:
                kwargs = dict({'widget': widgets.AdminTextInputWidget}, **kwargs)
            return formfield(db_field, **kwargs)

        # If we've got overrides for the formfield defined, use 'em. **kwargs
        # passed to formfield_for_dbfield override the defaults.
        for klass in db_field.__class__.mro():
            if klass in self.formfield_overrides:
                kwargs = dict(self.formfield_overrides[klass], **kwargs)
                return formfield(db_field, **kwargs)

        # For any other type of field, just call its formfield() method.
        return formfield(db_field, **kwargs)

    def formfield_for_choice_field(self, db_field, request=None, **kwargs):
        """
        Get a form Field for a database Field that has declared choices.
        """
        # If the field is named as a radio_field, use a RadioSelect
        if db_field.name in self.radio_fields:
            # Avoid stomping on custom widget/choices arguments.
            if 'widget' not in kwargs:
                kwargs['widget'] = widgets.AdminRadioSelect(attrs={
                    'class': get_ul_class(self.radio_fields[db_field.name]),
                })
            if 'choices' not in kwargs:
                kwargs['choices'] = db_field.get_choices(
                    include_blank = db_field.blank,
                    blank_choice=[('', _('None'))]
                )
        return formfield(db_field, **kwargs)


    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        """
        Get a form Field for a ManyToManyField.
        """
        db = kwargs.get('using')

        if db_field.name in self.raw_id_fields:
            kwargs['widget'] = widgets.ManyToManyRawIdWidget(db_field.rel, using=db)
            kwargs['help_text'] = ''
        elif db_field.name in (list(self.filter_vertical) + list(self.filter_horizontal)):
            kwargs['widget'] = widgets.FilteredSelectMultiple(pretty_name(db_field.name), (db_field.name in self.filter_vertical))

        return formfield(db_field, **kwargs)


@copy_class(ModelAdmin)
class DocumentAdmin(BaseDocumentAdmin):
    "Encapsulates all admin options and functionality for a given model."


    def __init__(self, model, admin_site):
        self.model = model
        self.opts = model._meta
        self.admin_site = admin_site
        super(DocumentAdmin, self).__init__()

    def get_inline_instances(self):
        for f in six.itervalues(self.model._fields):
            if not (isinstance(f, ListField) and isinstance(getattr(f, 'field', None), EmbeddedDocumentField)) and not isinstance(f, EmbeddedDocumentField):
                continue
            # Should only reach here if there is an embedded document...
            if f.name in self.exclude:
                continue
            document = self.model()
            if hasattr(f, 'field') and f.field is not None:
                embedded_document = f.field.document_type
            elif hasattr(f, 'document_type'):
                embedded_document = f.document_type
            else:
                # For some reason we found an embedded field were either
                # the field attribute or the field's document type is None.
                # This shouldn't happen, but apparently does happen:
                # https://github.com/jschrewe/django-mongoadmin/issues/4
                # The solution for now is to ignore that field entirely.
                continue
            inline_admin = EmbeddedStackedDocumentAdmin
            # check if there is an admin for the embedded document in
            # self.inlines. If there is, use this, else use default.
            for inline_class in self.inlines:
                if inline_class.document == embedded_document:
                    inline_admin = inline_class
            inline_instance = inline_admin(f, document, self.admin_site)
            # if f is an EmbeddedDocumentField set the maximum allowed form instances to one
            if isinstance(f, EmbeddedDocumentField):
                inline_instance.max_num = 1
                # exclude field from normal form
                if f.name not in self.exclude:
                    self.exclude.append(f.name)
            if f.name == 'created_at' and f.name not in self.exclude:
                self.exclude.append(f.name)
            self.inline_instances.append(inline_instance)


    def get_form(self, request, obj=None, **kwargs):
        """
        Returns a Form class for use in the admin add view. This is used by
        add_view and change_view.
        """
        if self.declared_fieldsets:
            fields = flatten_fieldsets(self.declared_fieldsets)
        else:
            fields = None
        if self.exclude is None:
            exclude = []
        else:
            exclude = list(self.exclude)
        exclude.extend(kwargs.get("exclude", []))
        exclude.extend(self.get_readonly_fields(request, obj))
        # if exclude is an empty list we pass None to be consistant with the
        # default on modelform_factory
        exclude = exclude or None
        defaults = {
            "form": self.form,
            "fields": fields,
            "exclude": exclude,
            "formfield_callback": curry(self.formfield_for_dbfield, request=request),
        }
        defaults.update(kwargs)
        document = self.model()
        return documentform_factory(document, **defaults)


    def get_object(self, request, object_id):
        """
        Returns an instance matching the primary key provided. ``None``  is
        returned if no match is found (or the object_id failed validation
        against the primary key field).
        """
        queryset = self.queryset(request)
        model = queryset._document
        try:
            object_id = model._meta.pk.to_python(object_id)
            return queryset.get(pk=object_id)
        except (model.DoesNotExist, ValidationError):
            return None

    def get_changelist_form(self, request, **kwargs):
        """
        Returns a Form class for use in the Formset on the changelist page.
        """
        defaults = {
            "formfield_callback": curry(self.formfield_for_dbfield, request=request),
        }
        defaults.update(kwargs)
        return documentform_factory(self.model, **defaults)

    def get_changelist_formset(self, request, **kwargs):
        """
        Returns a FormSet class for use on the changelist page if list_editable
        is used.
        """
        defaults = {
            "formfield_callback": curry(self.formfield_for_dbfield, request=request),
        }
        defaults.update(kwargs)
        return modelformset_factory(self.model,
            self.get_changelist_form(request), extra=0,
            fields=self.list_editable, **defaults)


    def log_addition(self, request, object):
        """
        Log that an object has been successfully added.

        The default implementation creates an admin LogEntry object.
        """
        if not self.log:
            return
        from django.contrib.admin.models import LogEntry, ADDITION
        LogEntry.objects.log_action(
            user_id         = request.user.pk,
            content_type_id = None,
            object_id       = object.pk,
            object_repr     = force_text(object),
            action_flag     = ADDITION
        )

    def log_change(self, request, object, message):
        """
        Log that an object has been successfully changed.

        The default implementation creates an admin LogEntry object.
        """
        if not self.log:
            return
        from django.contrib.admin.models import LogEntry, CHANGE
        LogEntry.objects.log_action(
            user_id         = request.user.pk,
            content_type_id = None,
            object_id       = object.pk,
            object_repr     = force_text(object),
            action_flag     = CHANGE,
            change_message  = message
        )

    def log_deletion(self, request, object, object_repr):
        """
        Log that an object will be deleted. Note that this method is called
        before the deletion.

        The default implementation creates an admin LogEntry object.
        """
        if not self.log:
            return
        from django.contrib.admin.models import LogEntry, DELETION
        LogEntry.objects.log_action(
            user_id         = request.user.id,
            content_type_id = None,
            object_id       = object.pk,
            object_repr     = object_repr,
            action_flag     = DELETION
        )


    @csrf_protect_m
    def changeform_view(self, request, object_id, extra_context=None):
        "The 'change' admin view for this model."
        model = self.model
        opts = model._meta

        obj = self.get_object(request, unquote(object_id))

        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {'name': force_text(opts.verbose_name), 'key': escape(object_id)})

        if request.method == 'POST' and "_saveasnew" in request.POST:
            return self.add_view(request, form_url='../add/')

        DocumentForm = self.get_form(request, obj)
        formsets = []
        # TODO: Something is wrong if formsets are invalid
        if request.method == 'POST':
            form = DocumentForm(request.POST, request.FILES, instance=obj)
            if form.is_valid():
                form_validated = True
                new_object = self.save_form(request, form, change=True)
            else:
                form_validated = False
                new_object = obj
            prefixes = {}
            for FormSet, inline in zip(self.get_formsets(request, new_object),
                                       self.inline_instances):
                prefix = FormSet.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = FormSet(request.POST, request.FILES,
                                  instance=new_object, prefix=prefix,
                                  queryset=inline.queryset(request))

                if formset.is_valid() and form_validated:
                    if isinstance(inline, EmbeddedDocumentAdmin):
                        embedded_object_list = formset.save()
                        if isinstance(inline.field, ListField):
                            setattr(new_object, inline.rel_name, embedded_object_list)
                        elif len(embedded_object_list) > 0:
                            setattr(new_object, inline.rel_name, embedded_object_list[0])
                        else:
                            setattr(new_object, inline.rel_name, None)
                    else:
                        formset.save()

            if all_valid(formsets) and form_validated:
                self.save_model(request, new_object, form, change=True)
                for formset in formsets:
                    self.save_formset(request, form, formset, change=True)

                change_message = self.construct_change_message(request, form, formsets)
                self.log_change(request, new_object, change_message)
                return self.response_change(request, new_object)

        else:
            form = DocumentForm(instance=obj)
            prefixes = {}
            # set the actual parent document on the inline admins
            for FormSet, inline in zip(self.get_formsets(request, obj), self.inline_instances):
                inline.parent_document = obj
                prefix = FormSet.get_default_prefix()
                prefixes[prefix] = prefixes.get(prefix, 0) + 1
                if prefixes[prefix] != 1:
                    prefix = "%s-%s" % (prefix, prefixes[prefix])
                formset = FormSet(instance=obj, prefix=prefix,
                                  queryset=inline.queryset(request))
                formsets.append(formset)

        adminForm = AdminForm(form, self.get_fieldsets(request, obj),
            self.prepopulated_fields, self.get_readonly_fields(request, obj),
            model_admin=self)
        media = self.media + adminForm.media

        inline_admin_formsets = []
        for inline, formset in zip(self.inline_instances, formsets):
            fieldsets = list(inline.get_fieldsets(request, obj))
            readonly = list(inline.get_readonly_fields(request, obj))

            inline_admin_formset = mongodb_helpers.InlineAdminFormSet(inline, formset,
                fieldsets, readonly, model_admin=self)

            inline_admin_formsets.append(inline_admin_formset)
            media = media + inline_admin_formset.media

        context = {
            'title': _('Change %s') % force_text(opts.verbose_name),
            'adminform': adminForm,
            'object_id': object_id,
            'original': obj,
            'is_popup': "_popup" in request.REQUEST,
            'media': mark_safe(media),
            'inline_admin_formsets': inline_admin_formsets,
            'errors': helpers.AdminErrorList(form, formsets),
            'root_path': self.admin_site.root_path,
            'app_label': opts.app_label,
        }
        context.update(extra_context or {})
        return self.render_change_form(request, context, change=True, obj=obj)
# XXX: stop here

    @csrf_protect_m
    def delete_view(self, request, object_id, extra_context=None):
        "The 'delete' admin view for this model."
        opts = self.model._meta
        app_label = opts.app_label

        obj = self.get_object(request, unquote(object_id))

        if not self.has_delete_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            raise Http404(_('%(name)s object with primary key %(key)r does not exist.') % {'name': force_text(opts.verbose_name), 'key': escape(object_id)})

        #using = router.db_for_write(self.model)

        # Populate deleted_objects, a data structure of all related objects that
        # will also be deleted.
        print("FIXME: Need to delete nested objects.")
        #(deleted_objects, perms_needed, protected) = get_deleted_objects(
        #    [obj], opts, request.user, self.admin_site, using)

        if request.POST: # The user has already confirmed the deletion.
            #if perms_needed:
            #    raise PermissionDenied
            obj_display = force_text(obj)
            self.log_deletion(request, obj, obj_display)
            self.delete_model(request, obj)

            self.message_user(request, _('The %(name)s "%(obj)s" was deleted successfully.') % {'name': force_text(opts.verbose_name), 'obj': force_text(obj_display)})

            if not self.has_change_permission(request, None):
                return HttpResponseRedirect("../../../../")
            return HttpResponseRedirect("../../")

        object_name = force_text(opts.verbose_name)

        #if perms_needed or protected:
        #    title = _("Cannot delete %(name)s") % {"name": object_name}
        #else:
        title = _("Are you sure?")

        context = {
            "title": title,
            "object_name": object_name,
            "object": obj,
            #"deleted_objects": deleted_objects,
            #"perms_lacking": perms_needed,
            #"protected": protected,
            "opts": opts,
            "root_path": self.admin_site.root_path,
            "app_label": app_label,
        }
        context.update(extra_context or {})
        context_instance = template.RequestContext(request, current_app=self.admin_site.name)
        return render_to_response(self.delete_confirmation_template or [
            "admin/%s/%s/delete_confirmation.html" % (app_label, opts.object_name.lower()),
            "admin/%s/delete_confirmation.html" % app_label,
            "admin/delete_confirmation.html"
        ], context, context_instance=context_instance)

    def history_view(self, request, object_id, extra_context=None):
        "The 'history' admin view for this model."
        from django.contrib.admin.models import LogEntry
        from django.contrib.contenttypes.models import ContentType
        model = self.model
        opts = model._meta
        app_label = opts.app_label
        action_list = LogEntry.objects.filter(
            object_id = object_id,
            content_type__id__exact = ContentType.objects.get_for_model(model).id
        ).select_related().order_by('action_time')
        # If no history was found, see whether this object even exists.
        obj = get_object_or_404(model, pk=unquote(object_id))
        context = {
            'title': _('Change history: %s') % force_text(obj),
            'action_list': action_list,
            'module_name': capfirst(force_text(opts.verbose_name_plural)),
            'object': obj,
            'root_path': self.admin_site.root_path,
            'app_label': app_label,
        }
        context.update(extra_context or {})
        context_instance = template.RequestContext(request, current_app=self.admin_site.name)
        return render_to_response(self.object_history_template or [
            "admin/%s/%s/object_history.html" % (app_label, opts.object_name.lower()),
            "admin/%s/object_history.html" % app_label,
            "admin/object_history.html"
        ], context, context_instance=context_instance)


class InlineDocumentAdmin(BaseDocumentAdmin):
    """
    Options for inline editing of ``model`` instances.

    Provide ``name`` to specify the attribute name of the ``ForeignKey`` from
    ``model`` to its parent. This is required if ``model`` has more than one
    ``ForeignKey`` to its parent.
    """
    document = None
    fk_name = None
    formset = BaseInlineDocumentFormSet
    extra = 1
    max_num = None
    template = None
    verbose_name = None
    verbose_name_plural = None
    can_delete = True

    def __init__(self, parent_document, admin_site):
        self.admin_site = admin_site
        self.parent_document = parent_document
        self.opts = self.model._meta

        super(InlineDocumentAdmin, self).__init__()

        if self.verbose_name is None:
            self.verbose_name = self.model._meta.verbose_name

        if self.verbose_name_plural is None:
            self.verbose_name_plural = self.model._meta.verbose_name_plural

    def _media(self):
        from django.conf import settings
        js = ['js/jquery.min.js', 'js/jquery.init.js', 'js/inlines.min.js']
        if self.prepopulated_fields:
            js.append('js/urlify.js')
            js.append('js/prepopulate.min.js')
        if self.filter_vertical or self.filter_horizontal:
            js.extend(['js/SelectBox.js' , 'js/SelectFilter2.js'])
        return forms.Media(js=['%s%s' % (settings.ADMIN_MEDIA_PREFIX, url) for url in js])
    media = property(_media)

    def get_formset(self, request, obj=None, **kwargs):
        """Returns a BaseInlineFormSet class for use in admin add/change views."""
        if self.declared_fieldsets:
            fields = flatten_fieldsets(self.declared_fieldsets)
        else:
            fields = None
        if self.exclude is None:
            exclude = []
        else:
            exclude = list(self.exclude)
        exclude.extend(kwargs.get("exclude", []))
        exclude.extend(self.get_readonly_fields(request, obj))
        # if exclude is an empty list we use None, since that's the actual
        # default
        exclude = exclude or None
        defaults = {
            "form": self.form,
            "formset": self.formset,
            "fields": fields,
            "exclude": exclude,
            "formfield_callback": curry(self.formfield_for_dbfield, request=request),
            "extra": self.extra,
            "max_num": self.max_num,
            "can_delete": self.can_delete,
        }
        defaults.update(kwargs)
        return inlineformset_factory(self.model, **defaults)

    def get_fieldsets(self, request, obj=None):
        if self.declared_fieldsets:
            return self.declared_fieldsets
        form = self.get_formset(request).form
        fields = form.base_fields.keys() + list(self.get_readonly_fields(request, obj))
        return [(None, {'fields': fields})]

class EmbeddedDocumentAdmin(InlineDocumentAdmin):
    def __init__(self, field, parent_document, admin_site):
        if hasattr(field, 'field'):
            self.model = field.field.document_type
        else:
            self.model = field.document_type
        self.doc_list = getattr(parent_document, field.name)
        self.field = field
        if not isinstance(self.doc_list, list):
            self.doc_list = []
        self.rel_name = field.name

        if self.verbose_name is None:
            self.verbose_name = "Field: %s (Document: %s)" % (capfirst(field.name), self.model._meta.verbose_name)

        if self.verbose_name_plural is None:
            self.verbose_name_plural = "Field: %s (Document:  %s)" % (capfirst(field.name), self.model._meta.verbose_name_plural)

        super(EmbeddedDocumentAdmin, self).__init__(parent_document, admin_site)

    def queryset(self, request):
        if isinstance(self.field, ListField): # list field
            self.doc_list = getattr(self.parent_document, self.rel_name)
        else: # embedded field
            emb_doc = getattr(self.parent_document, self.rel_name)
            if emb_doc is None:
                self.doc_list = []
            else:
                self.doc_list = [emb_doc]
        return self.doc_list

class StackedDocumentInline(InlineDocumentAdmin):
    template = 'admin/edit_inline/stacked.html'

class EmbeddedStackedDocumentAdmin(EmbeddedDocumentAdmin):
    template = 'admin/edit_inline/stacked.html'

class TabularDocumentInline(InlineDocumentAdmin):
    template = 'admin/edit_inline/tabular.html'
