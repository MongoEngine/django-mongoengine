import operator
from functools import partial, partialmethod, reduce

from django import forms
from django.apps import apps
from django.conf import settings
from django.contrib.admin import helpers, widgets
from django.contrib.admin.exceptions import DisallowedModelAdminToField
from django.contrib.admin.options import (
    IS_POPUP_VAR,
    TO_FIELD_VAR,
    csrf_protect_m,
    get_ul_class,
)
from django.contrib.admin.utils import flatten_fieldsets, get_deleted_objects, unquote
from django.core.exceptions import PermissionDenied
from django.forms.formsets import all_valid
from django.forms.models import modelform_defines_fields
from django.forms.utils import pretty_name
from django.http import Http404
from django.template.response import TemplateResponse
from django.urls import reverse
from django.utils.encoding import force_str
from django.utils.html import escape
from django.utils.text import capfirst
from django.utils.translation import gettext as _
from mongoengine import Q

from django_mongoengine.fields import (
    EmbeddedDocumentField,
    ListField,
    ReferenceField,
    StringField,
)
from django_mongoengine.forms.documents import (
    BaseInlineDocumentFormSet,
    DocumentForm,
    documentform_factory,
    documentformset_factory,
    inlineformset_factory,
)
from django_mongoengine.mongo_admin.util import RelationWrapper
from django_mongoengine.paginator import Paginator
from django_mongoengine.utils.monkey import get_patched_django_module
from django_mongoengine.utils.wrappers import copy_class


def get_content_type_for_model(obj):
    return apps.get_model("contenttypes.ContentType")()


djmod = get_patched_django_module(
    "django.contrib.admin.options",
    get_content_type_for_model=get_content_type_for_model,
)


class BaseDocumentAdmin(djmod.ModelAdmin):
    """Functionality common to both ModelAdmin and InlineAdmin."""

    form = DocumentForm
    paginator = Paginator

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
            form_field = db_field.formfield(**kwargs)
            if db_field.name not in self.raw_id_fields:
                related_modeladmin = self.admin_site._registry.get(db_field.document_type)
                can_add_related = bool(
                    related_modeladmin and related_modeladmin.has_add_permission(request)
                )
                form_field.widget = widgets.RelatedFieldWidgetWrapper(
                    form_field.widget,
                    RelationWrapper(db_field.document_type),
                    self.admin_site,
                    can_add_related=can_add_related,
                )
                return form_field

        if isinstance(db_field, StringField):
            if db_field.max_length is None:
                kwargs = dict({"widget": widgets.AdminTextareaWidget}, **kwargs)
            else:
                kwargs = dict({"widget": widgets.AdminTextInputWidget}, **kwargs)
            return db_field.formfield(**kwargs)

        # If we've got overrides for the formfield defined, use 'em. **kwargs
        # passed to formfield_for_dbfield override the defaults.
        for klass in db_field.__class__.mro():
            if klass in self.formfield_overrides:
                kwargs = dict(self.formfield_overrides[klass], **kwargs)
                return db_field.formfield(**kwargs)

        # For any other type of field, just call its formfield() method.
        return db_field.formfield(**kwargs)

    def formfield_for_choice_field(self, db_field, request=None, **kwargs):
        """
        Get a form Field for a database Field that has declared choices.
        """
        # If the field is named as a radio_field, use a RadioSelect
        if db_field.name in self.radio_fields:
            # Avoid stomping on custom widget/choices arguments.
            if "widget" not in kwargs:
                kwargs["widget"] = widgets.AdminRadioSelect(
                    attrs={
                        "class": get_ul_class(self.radio_fields[db_field.name]),
                    }
                )
            if "choices" not in kwargs:
                kwargs["choices"] = db_field.get_choices(
                    include_blank=db_field.blank, blank_choice=[("", _("None"))]
                )
        return db_field.formfield(**kwargs)

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        """
        Get a form Field for a ManyToManyField.
        """
        db = kwargs.get("using")

        if db_field.name in self.raw_id_fields:
            kwargs["widget"] = widgets.ManyToManyRawIdWidget(db_field.rel, using=db)
            kwargs["help_text"] = ""
        elif db_field.name in (list(self.filter_vertical) + list(self.filter_horizontal)):
            kwargs["widget"] = widgets.FilteredSelectMultiple(
                pretty_name(db_field.name), (db_field.name in self.filter_vertical)
            )

        return db_field.formfield(**kwargs)

    def get_view_on_site_url(self, obj=None):
        if obj is None or not self.view_on_site:
            return None

        if callable(self.view_on_site):
            return self.view_on_site(obj)
        elif self.view_on_site and hasattr(obj, "get_absolute_url"):
            # use the ContentType lookup if view_on_site is True
            return reverse("admin:view_on_site", kwargs={"content_type_id": 0, "object_id": obj.pk})


@copy_class(djmod.ModelAdmin)
class DocumentAdmin(BaseDocumentAdmin):
    "Encapsulates all admin options and functionality for a given model."

    paginator = Paginator

    def __init__(self, model, admin_site):
        self.model = model
        self.opts = model._meta
        self.admin_site = admin_site
        super().__init__(model, admin_site)
        self.log = (
            not settings.DATABASES.get("default", {})
            .get("ENGINE", "django.db.backends.dummy")
            .endswith("dummy")
        )

    # XXX: add inline init somewhere
    def _get_inline_instances(self):
        for f in self.model._fields.values():
            if not (
                isinstance(f, ListField)
                and isinstance(getattr(f, "field", None), EmbeddedDocumentField)
            ) and not isinstance(f, EmbeddedDocumentField):
                continue
            # Should only reach here if there is an embedded document...
            if f.name in self.exclude:
                continue
            document = self.model()
            if hasattr(f, "field") and f.field is not None:
                embedded_document = f.field.document_type
            elif hasattr(f, "document_type"):
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
            if f.name == "created_at" and f.name not in self.exclude:
                self.exclude.append(f.name)
            self.inline_instances.append(inline_instance)

    def get_changelist_form(self, request, **kwargs):
        """
        Returns a Form class for use in the Formset on the changelist page.
        """
        defaults = {
            "formfield_callback": partial(self.formfield_for_dbfield, request=request),
        }
        defaults.update(kwargs)
        if defaults.get("fields") is None and not modelform_defines_fields(defaults.get("form")):
            defaults["fields"] = forms.ALL_FIELDS

        return documentform_factory(self.model, **defaults)

    def get_changelist_formset(self, request, **kwargs):
        """
        Returns a FormSet class for use on the changelist page if list_editable
        is used.
        """
        defaults = {
            "formfield_callback": partial(self.formfield_for_dbfield, request=request),
        }
        defaults.update(kwargs)
        return documentformset_factory(
            self.model,
            self.get_changelist_form(request),
            extra=0,
            fields=self.list_editable,
            **defaults,
        )

    def get_search_results(self, request, queryset, search_term):
        """
        Return a tuple containing a queryset to implement the search
        and a boolean indicating if the results may contain duplicates.
        """

        def construct_search(field_name):
            if field_name.startswith("^"):
                return "%s__istartswith" % field_name[1:]
            elif field_name.startswith("="):
                return "%s__iexact" % field_name[1:]
            # No __search for mongoengine
            # elif field_name.startswith('@'):
            #    return "%s__search" % field_name[1:]
            else:
                return "%s__icontains" % field_name

        search_fields = self.get_search_fields(request)

        if search_fields and search_term:
            orm_lookups = [construct_search(str(search_field)) for search_field in search_fields]
            for bit in search_term.split():
                or_queries = [Q(**{orm_lookup: bit}) for orm_lookup in orm_lookups]
                queryset = queryset.filter(reduce(operator.or_, or_queries))

        return queryset, False

    def get_changelist(self, request, **kwargs):
        """
        Returns the ChangeList class for use on the changelist page.
        """
        from django_mongoengine.mongo_admin.views import DocumentChangeList

        return DocumentChangeList

    def log_addition(self, request, object, message):
        """
        Log that an object has been successfully added.
        The default implementation creates an admin LogEntry object.
        """
        if not self.log:
            return
        super().log_addition(request, object, message)

    def log_change(self, request, object, message):
        """
        Log that an object has been successfully changed.
        The default implementation creates an admin LogEntry object.
        """
        if not self.log:
            return
        super().log_change(request, object, message)

    def log_deletion(self, request, object, object_repr):
        """
        Log that an object will be deleted. Note that this method is called
        before the deletion.
        The default implementation creates an admin LogEntry object.
        """
        if not self.log:
            return
        super().log_deletion(request, object, object_repr)

    @property
    def media(self):
        return djmod.ModelAdmin.media.fget(self)

    @csrf_protect_m
    def changeform_view(self, request, object_id=None, form_url="", extra_context=None):
        to_field = request.POST.get(TO_FIELD_VAR, request.GET.get(TO_FIELD_VAR))
        if to_field and not self.to_field_allowed(request, to_field):
            raise DisallowedModelAdminToField("The field %s cannot be referenced." % to_field)

        model = self.model
        opts = model._meta

        if request.method == "POST" and "_saveasnew" in request.POST:
            object_id = None

        add = object_id is None

        if add:
            if not self.has_add_permission(request):
                raise PermissionDenied
            obj = None

        else:
            obj = self.get_object(request, unquote(object_id), to_field)

            if not self.has_change_permission(request, obj):
                raise PermissionDenied

            if obj is None:
                raise Http404(
                    _("%(name)s object with primary key %(key)r does not exist.")
                    % {"name": force_str(opts.verbose_name), "key": escape(object_id)}
                )

        ModelForm = self.get_form(request, obj)
        form_validated = False

        if request.method == "POST":
            form = ModelForm(request.POST, request.FILES, instance=obj)
            if form.is_valid():
                form_validated = True
                new_object = self.save_form(request, form, change=not add)
            else:
                form_validated = False
                new_object = form.instance
            formsets, inline_instances = self._create_formsets(request, new_object, change=not add)
            if all_valid(formsets) and form_validated:
                self.save_model(request, new_object, form, not add)
                self.save_related(request, form, formsets, not add)
                change_message = self.construct_change_message(request, form, formsets, add)
                if add:
                    self.log_addition(request, new_object, change_message)
                    return self.response_add(request, new_object)
                else:
                    self.log_change(request, new_object, change_message)
                    return self.response_change(request, new_object)
            else:
                form_validated = False
        else:
            if add:
                initial = self.get_changeform_initial_data(request)
                form = ModelForm(initial=initial)
                formsets, inline_instances = self._create_formsets(
                    request, form.instance, change=False
                )
            else:
                form = ModelForm(instance=obj)
                formsets, inline_instances = self._create_formsets(request, obj, change=True)

        adminForm = helpers.AdminForm(
            form,
            list(self.get_fieldsets(request, obj)),
            self.get_prepopulated_fields(request, obj),
            self.get_readonly_fields(request, obj),
            model_admin=self,
        )
        media = self.media + adminForm.media

        inline_formsets = self.get_inline_formsets(request, formsets, inline_instances, obj)
        for inline_formset in inline_formsets:
            media = media + inline_formset.media

        context = dict(
            self.admin_site.each_context(request),
            title=(_("Add %s") if add else _("Change %s")) % force_str(opts.verbose_name),
            adminform=adminForm,
            object_id=object_id,
            original=obj,
            is_popup=(IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET),
            to_field=to_field,
            media=media,
            inline_admin_formsets=inline_formsets,
            errors=helpers.AdminErrorList(form, formsets),
            preserved_filters=self.get_preserved_filters(request),
        )

        # Hide the "Save" and "Save and continue" buttons if "Save as New" was
        # previously chosen to prevent the interface from getting confusing.
        if request.method == "POST" and not form_validated and "_saveasnew" in request.POST:
            context["show_save"] = False
            context["show_save_and_continue"] = False
            # Use the change template instead of the add template.
            add = False

        context.update(extra_context or {})

        return self.render_change_form(
            request, context, add=add, change=not add, obj=obj, form_url=form_url
        )

    @csrf_protect_m
    def delete_view(self, request, object_id, extra_context=None):
        "The 'delete' admin view for this model."
        opts = self.model._meta
        app_label = opts.app_label

        to_field = request.POST.get(TO_FIELD_VAR, request.GET.get(TO_FIELD_VAR))
        if to_field and not self.to_field_allowed(request, to_field):
            raise DisallowedModelAdminToField("The field %s cannot be referenced." % to_field)

        obj = self.get_object(request, unquote(object_id), to_field)

        if not self.has_delete_permission(request, obj):
            raise PermissionDenied

        if obj is None:
            raise Http404(
                _("%(name)s object with primary key %(key)r does not exist.")
                % {"name": force_str(opts.verbose_name), "key": escape(object_id)}
            )

        # Populate deleted_objects, a data structure of all related objects that
        # will also be deleted.
        (deleted_objects, model_count, perms_needed, protected) = get_deleted_objects(
            [obj], request, self.admin_site
        )

        if request.POST:  # The user has already confirmed the deletion.
            if perms_needed:
                raise PermissionDenied
            obj_display = force_str(obj)
            attr = str(to_field) if to_field else opts.pk.attname
            obj_id = obj.serializable_value(attr)
            self.log_deletion(request, obj, obj_display)
            self.delete_model(request, obj)

            return self.response_delete(request, obj_display, obj_id)

        object_name = force_str(opts.verbose_name)

        if perms_needed or protected:
            title = _("Cannot delete %(name)s") % {"name": object_name}
        else:
            title = _("Are you sure?")

        context = dict(
            self.admin_site.each_context(request),
            title=title,
            object_name=object_name,
            object=obj,
            deleted_objects=deleted_objects,
            model_count=dict(model_count).items(),
            perms_lacking=perms_needed,
            protected=protected,
            opts=opts,
            app_label=app_label,
            preserved_filters=self.get_preserved_filters(request),
            is_popup=(IS_POPUP_VAR in request.POST or IS_POPUP_VAR in request.GET),
            to_field=to_field,
        )
        context.update(extra_context or {})

        return self.render_delete_form(request, context)

    def history_view(self, request, object_id, extra_context=None):
        "The 'history' admin view for this model."
        from django.contrib.admin.models import LogEntry

        # First check if the user can see this history.
        model = self.model
        obj = self.get_object(request, unquote(object_id))
        if obj is None:
            raise Http404(
                _("%(name)s object with primary key %(key)r does not exist.")
                % {
                    "name": force_str(model._meta.verbose_name),
                    "key": escape(object_id),
                }
            )

        if not self.has_change_permission(request, obj):
            raise PermissionDenied

        # Then get the history for this object.
        opts = model._meta
        app_label = opts.app_label
        action_list = (
            LogEntry.objects.filter(
                object_id=unquote(object_id), content_type=get_content_type_for_model(model)
            )
            .select_related()
            .order_by("action_time")
        )

        context = dict(
            self.admin_site.each_context(request),
            title=_("Change history: %s") % force_str(obj),
            action_list=action_list,
            module_name=capfirst(force_str(opts.verbose_name_plural)),
            object=obj,
            opts=opts,
            preserved_filters=self.get_preserved_filters(request),
        )
        context.update(extra_context or {})

        request.current_app = self.admin_site.name

        return TemplateResponse(
            request,
            self.object_history_template
            or [
                "admin/%s/%s/object_history.html" % (app_label, opts.model_name),
                "admin/%s/object_history.html" % app_label,
                "admin/object_history.html",
            ],
            context,
        )


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

        super().__init__()

        if self.verbose_name is None:
            self.verbose_name = self.model._meta.verbose_name

        if self.verbose_name_plural is None:
            self.verbose_name_plural = self.model._meta.verbose_name_plural

    media = djmod.ModelAdmin.media

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
            "formfield_callback": partialmethod(self.formfield_for_dbfield, request=request),
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
        return [(None, {"fields": fields})]


class EmbeddedDocumentAdmin(InlineDocumentAdmin):
    def __init__(self, field, parent_document, admin_site):
        if hasattr(field, "field"):
            self.model = field.field.document_type
        else:
            self.model = field.document_type
        self.doc_list = getattr(parent_document, field.name)
        self.field = field
        if not isinstance(self.doc_list, list):
            self.doc_list = []
        self.rel_name = field.name

        if self.verbose_name is None:
            self.verbose_name = "Field: %s (Document: %s)" % (
                capfirst(field.name),
                self.model._meta.verbose_name,
            )

        if self.verbose_name_plural is None:
            self.verbose_name_plural = "Field: %s (Document:  %s)" % (
                capfirst(field.name),
                self.model._meta.verbose_name_plural,
            )

        super().__init__(parent_document, admin_site)

    def queryset(self, request):
        if isinstance(self.field, ListField):  # list field
            self.doc_list = getattr(self.parent_document, self.rel_name)
        else:  # embedded field
            emb_doc = getattr(self.parent_document, self.rel_name)
            if emb_doc is None:
                self.doc_list = []
            else:
                self.doc_list = [emb_doc]
        return self.doc_list


class StackedDocumentInline(InlineDocumentAdmin):
    template = "admin/edit_inline/stacked.html"


class EmbeddedStackedDocumentAdmin(EmbeddedDocumentAdmin):
    template = "admin/edit_inline/stacked.html"


class TabularDocumentInline(InlineDocumentAdmin):
    template = "admin/edit_inline/tabular.html"
