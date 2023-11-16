from django.contrib.admin.helpers import AdminField
from django.contrib.admin.helpers import AdminForm as DjangoAdminForm
from django.contrib.admin.helpers import AdminReadonlyField as DjangoAdminReadonlyField
from django.contrib.admin.helpers import Fieldline as DjangoFieldLine
from django.contrib.admin.helpers import Fieldset as DjangoFieldSet
from django.contrib.admin.helpers import InlineAdminForm as DjangoInlineAdminForm
from django.contrib.admin.helpers import InlineAdminFormSet as DjangoInlineAdminFormSet
from django.contrib.admin.helpers import InlineFieldset as DjangoInlineFieldset
from django.contrib.admin.utils import lookup_field
from django.core.exceptions import ObjectDoesNotExist
from django.utils.encoding import smart_str
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

from django_mongoengine.mongo_admin.util import (
    display_for_field,
    help_text_for_field,
    label_for_field,
)


class AdminForm(DjangoAdminForm):
    def __iter__(self):
        for name, options in self.fieldsets:
            yield Fieldset(
                self.form,
                name,
                readonly_fields=self.readonly_fields,
                model_admin=self.model_admin,
                **options,
            )


class Fieldset(DjangoFieldSet):
    def __iter__(self):
        for field in self.fields:
            yield Fieldline(self.form, field, self.readonly_fields, model_admin=self.model_admin)


class Fieldline(DjangoFieldLine):
    def __iter__(self):
        for i, field in enumerate(self.fields):
            if field in self.readonly_fields:
                yield AdminReadonlyField(
                    self.form, field, is_first=(i == 0), model_admin=self.model_admin
                )
            else:
                yield AdminField(self.form, field, is_first=(i == 0))


class AdminReadonlyField(DjangoAdminReadonlyField):
    def __init__(self, form, field, is_first, model_admin=None):
        label = label_for_field(field, form._meta.model, model_admin)
        # Make self.field look a little bit like a field. This means that
        # {{ field.name }} must be a useful class name to identify the field.
        # For convenience, store other field-related data here too.
        if callable(field):
            class_name = field.__name__ != "<lambda>" and field.__name__ or ""
        else:
            class_name = field
        self.field = {
            "name": class_name,
            "label": label,
            "field": field,
            "help_text": help_text_for_field(class_name, form._meta.model),
        }
        self.form = form
        self.model_admin = model_admin
        self.is_first = is_first
        self.is_checkbox = False
        self.is_readonly = True

    def contents(self):
        from django.contrib.admin.templatetags.admin_list import _boolean_icon

        field, obj, model_admin = self.field["field"], self.form.instance, self.model_admin
        try:
            f, attr, value = lookup_field(field, obj, model_admin)
        except (AttributeError, ValueError, ObjectDoesNotExist):
            result_repr = self.model_admin.get_empty_value_diplay()
        else:
            if f is None:
                boolean = getattr(attr, "boolean", False)
                if boolean:
                    result_repr = _boolean_icon(value)
                else:
                    result_repr = smart_str(value)
                    if getattr(attr, "allow_tags", False):
                        result_repr = mark_safe(result_repr)
            else:
                if value is None:
                    result_repr = self.model_admin.get_empty_value_diplay()
                # HERE WE NEED TO CHANGE THIS TEST
                # elif isinstance(f.rel, ManyToManyRel):
                #     result_repr = ", ".join(map(unicode, value.all()))
                else:
                    result_repr = display_for_field(value, f)
        return conditional_escape(result_repr)


class InlineAdminFormSet(DjangoInlineAdminFormSet):
    """
    A wrapper around an inline formset for use in the admin system.
    """

    def __iter__(self):
        for form, original in zip(self.formset.initial_forms, self.formset.get_queryset()):
            yield InlineAdminForm(
                self.formset,
                form,
                self.fieldsets,
                self.opts.prepopulated_fields,
                original,
                self.readonly_fields,
                model_admin=self.opts,
            )
        for form in self.formset.extra_forms:
            yield InlineAdminForm(
                self.formset,
                form,
                self.fieldsets,
                self.opts.prepopulated_fields,
                None,
                self.readonly_fields,
                model_admin=self.opts,
            )
        yield InlineAdminForm(
            self.formset,
            self.formset.empty_form,
            self.fieldsets,
            self.opts.prepopulated_fields,
            None,
            self.readonly_fields,
            model_admin=self.opts,
        )


class InlineAdminForm(DjangoInlineAdminForm, AdminForm):
    """
    A wrapper around an inline form for use in the admin system.
    """

    def __init__(
        self,
        formset,
        form,
        fieldsets,
        prepopulated_fields,
        original,
        readonly_fields=None,
        model_admin=None,
    ):
        self.formset = formset
        self.model_admin = model_admin
        self.original = original
        self.show_url = original and hasattr(original, "get_absolute_url")
        AdminForm.__init__(self, form, fieldsets, prepopulated_fields, readonly_fields, model_admin)

    def pk_field(self):
        # if there is no pk field then it's an embedded form so return none
        if hasattr(self.formset, "_pk_field"):
            return DjangoInlineAdminForm.pk_field(self)
        else:
            return None

    def __iter__(self):
        for name, options in self.fieldsets:
            yield InlineFieldset(
                self.formset,
                self.form,
                name,
                self.readonly_fields,
                model_admin=self.model_admin,
                **options,
            )


class InlineFieldset(DjangoInlineFieldset):
    def __iter__(self):
        fk = getattr(self.formset, "fk", None)
        for field in self.fields:
            if fk and fk.name == field:
                continue
            yield Fieldline(self.form, field, self.readonly_fields, model_admin=self.model_admin)
