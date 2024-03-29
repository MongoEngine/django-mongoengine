"""
Built-in, globally-available admin actions.
"""

from django import template
from django.contrib.admin import helpers
from django.contrib.admin.actions import delete_selected as django_delete_selected
from django.contrib.admin.utils import get_deleted_objects, model_ngettext
from django.core.exceptions import PermissionDenied
from django.db import models
from django.shortcuts import render_to_response
from django.utils.translation import gettext_lazy as _

from django_mongoengine.utils import force_str


def delete_selected(modeladmin, request, queryset):
    if issubclass(modeladmin.model, models.Model):
        return django_delete_selected(modeladmin, request, queryset)
    else:
        return _delete_selected(modeladmin, request, queryset)


def _delete_selected(modeladmin, request, queryset):
    """
    Default action which deletes the selected objects.

    This action first displays a confirmation page whichs shows all the
    deleteable objects, or, if the user has no permission one of the related
    childs (foreignkeys), a "permission denied" message.

    Next, it delets all selected objects and redirects back to the change list.
    """
    opts = modeladmin.model._meta
    app_label = opts.app_label

    # Check that the user has delete permission for the actual model
    if not modeladmin.has_delete_permission(request):
        raise PermissionDenied

    # Populate deletable_objects, a data structure of all related objects that
    # will also be deleted.
    # TODO: Permissions would be so cool...
    deletable_objects, perms_needed, protected = get_deleted_objects(
        queryset, request, modeladmin.admin_site
    )

    # The user has already confirmed the deletion.
    # Do the deletion and return a None to display the change list view again.
    if request.POST.get("post"):
        if perms_needed:
            raise PermissionDenied
        n = len(queryset)
        if n:
            for obj in queryset:
                obj_display = force_str(obj)
                modeladmin.log_deletion(request, obj, obj_display)
                # call the objects delete method to ensure signals are
                # processed.
                obj.delete()
            # This is what you get if you have to monkey patch every object in a changelist
            # No queryset object, I can tell ya. So we get a new one and delete that.
            # pk_list = [o.pk for o in queryset]
            # klass = queryset[0].__class__
            # qs = klass.objects.filter(pk__in=pk_list)
            # qs.delete()
            modeladmin.message_user(
                request,
                _("Successfully deleted %(count)d %(items)s.")
                % {"count": n, "items": model_ngettext(modeladmin.opts, n)},
            )
        # Return None to display the change list page again.
        return None

    if len(queryset) == 1:
        objects_name = force_str(opts.verbose_name)
    else:
        objects_name = force_str(opts.verbose_name_plural)

    if perms_needed or protected:
        title = _("Cannot delete %(name)s") % {"name": objects_name}
    else:
        title = _("Are you sure?")

    context = {
        "title": title,
        "objects_name": objects_name,
        "deletable_objects": [deletable_objects],
        "queryset": queryset,
        "perms_lacking": perms_needed,
        "protected": protected,
        "opts": opts,
        "root_path": modeladmin.admin_site.root_path,
        "app_label": app_label,
        "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
    }

    # Display the confirmation page
    return render_to_response(
        modeladmin.delete_selected_confirmation_template
        or [
            "admin/%s/%s/delete_selected_confirmation.html" % (app_label, opts.object_name.lower()),
            "admin/%s/delete_selected_confirmation.html" % app_label,
            "admin/delete_selected_confirmation.html",
        ],
        context,
        context_instance=template.RequestContext(request),
    )


delete_selected.short_description = _("Delete selected %(verbose_name_plural)s")
