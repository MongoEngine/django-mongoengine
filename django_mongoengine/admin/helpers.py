from django.contrib.admin.helpers import InlineAdminForm as DjangoInlineAdminForm
from django.contrib.admin.helpers import InlineAdminFormSet as DjangoInlineAdminFormSet
from django.contrib.admin.helpers import AdminForm

class InlineAdminFormSet(DjangoInlineAdminFormSet):
    """
    A wrapper around an inline formset for use in the admin system.
    """
    def __iter__(self):
        for form, original in zip(self.formset.initial_forms, self.formset.get_queryset()):
            yield InlineAdminForm(self.formset, form, self.fieldsets,
                self.opts.prepopulated_fields, original, self.readonly_fields,
                model_admin=self.opts)
        for form in self.formset.extra_forms:
            yield InlineAdminForm(self.formset, form, self.fieldsets,
                self.opts.prepopulated_fields, None, self.readonly_fields,
                model_admin=self.opts)
        yield InlineAdminForm(self.formset, self.formset.empty_form,
            self.fieldsets, self.opts.prepopulated_fields, None,
            self.readonly_fields, model_admin=self.opts)



class InlineAdminForm(DjangoInlineAdminForm):
    """
    A wrapper around an inline form for use in the admin system.
    """
    def __init__(self, formset, form, fieldsets, prepopulated_fields, original,
      readonly_fields=None, model_admin=None):
        self.formset = formset
        self.model_admin = model_admin
        self.original = original
        self.show_url = original and hasattr(original, 'get_absolute_url')
        AdminForm.__init__(self, form, fieldsets, prepopulated_fields,
            readonly_fields, model_admin)

    def pk_field(self):
        # if there is no pk field then it's an embedded form so return none
        if hasattr(self.formset, "_pk_field"):
            return super(InlineAdminForm, self).pk_field()
        else:
            return None


