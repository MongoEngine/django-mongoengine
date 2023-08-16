from django.core.exceptions import FieldDoesNotExist
from django.forms.utils import pretty_name
from django.utils import formats
from django.utils.encoding import smart_str
from mongoengine import fields


class RelationWrapper:
    """
    Wraps a document referenced from a ReferenceField with an Interface similiar to
    django's ForeignKeyField.rel
    """

    def __init__(self, document):
        self.to = document


def label_for_field(name, model, model_admin=None, return_attr=False):
    attr = None
    try:
        field = model._meta.get_field_by_name(name)[0]
        label = field.name.replace('_', ' ')
    except FieldDoesNotExist:
        if name == "__unicode__":
            label = force_str(model._meta.verbose_name)
        elif name == "__str__":
            label = smart_str(model._meta.verbose_name)
        else:
            if callable(name):
                attr = name
            elif model_admin is not None and hasattr(model_admin, name):
                attr = getattr(model_admin, name)
            elif hasattr(model, name):
                attr = getattr(model, name)
            else:
                message = "Unable to lookup '%s' on %s" % (name, model._meta.object_name)
                if model_admin:
                    message += " or %s" % (model_admin.__class__.__name__,)
                raise AttributeError(message)

            if hasattr(attr, "short_description"):
                label = attr.short_description
            elif callable(attr):
                if attr.__name__ == "<lambda>":
                    label = "--"
                else:
                    label = pretty_name(attr.__name__)
            else:
                label = pretty_name(name)
    if return_attr:
        return (label, attr)
    else:
        return label


def display_for_field(value, field):
    from django.contrib.admin.templatetags.admin_list import _boolean_icon
    from django.contrib.admin.views.main import EMPTY_CHANGELIST_VALUE

    # if field.flatchoices:
    #     return dict(field.flatchoices).get(value, EMPTY_CHANGELIST_VALUE)
    # NullBooleanField needs special-case null-handling, so it comes
    # before the general null test.
    if isinstance(field, fields.BooleanField):
        return _boolean_icon(value)
    elif value is None:
        return EMPTY_CHANGELIST_VALUE
    elif isinstance(field, fields.DateTimeField):
        return formats.localize(value)
    elif isinstance(field, fields.DecimalField):
        return formats.number_format(value, field.decimal_places)
    elif isinstance(field, fields.FloatField):
        return formats.number_format(value)
    else:
        return smart_str(value)


def help_text_for_field(name, model):
    try:
        help_text = model._meta.get_field_by_name(name)[0].help_text
    except FieldDoesNotExist:
        help_text = ""
    return smart_str(help_text, strings_only=True)
