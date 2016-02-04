from django.template import Library

from django.contrib.admin.templatetags.admin_list import (result_hidden_fields, ResultList, items_for_result,
                                                          result_headers)
from django.db.models.fields import FieldDoesNotExist

from django_mongoengine.forms.utils import patch_document

register = Library()

def serializable_value(self, field_name):
    """
    Returns the value of the field name for this instance. If the field is
    a foreign key, returns the id value, instead of the object. If there's
    no Field object with this name on the model, the model attribute's
    value is returned directly.

    Used to serialize a field's value (in the serializer, or form output,
    for example). Normally, you would just access the attribute directly
    and not use this method.
    """
    try:
        field = self._meta.get_field_by_name(field_name)[0]
    except FieldDoesNotExist:
        return getattr(self, field_name)
    return getattr(self, field.name)

def results(cl):
    """
    Just like the one from Django. Only we add a serializable_value method to
    the document, because Django expects it and mongoengine doesn't have it.
    """
    if cl.formset:
        for res, form in zip(cl.result_list, cl.formset.forms):
            patch_document(serializable_value, res)
            yield ResultList(form, items_for_result(cl, res, form))
    else:
        for res in cl.result_list:
            patch_document(serializable_value, res)
            yield ResultList(None, items_for_result(cl, res, None))

def document_result_list(cl):
    """
    Displays the headers and data list together
    """
    headers = list(result_headers(cl))
    try:
        num_sorted_fields = 0
        for h in headers:
            if h['sortable'] and h['sorted']:
                num_sorted_fields += 1
    except KeyError:
        pass

    return {'cl': cl,
            'result_hidden_fields': list(result_hidden_fields(cl)),
            'result_headers': headers,
            'num_sorted_fields': num_sorted_fields,
            'results': list(results(cl))}
result_list = register.inclusion_tag("admin/change_list_results.html")(document_result_list)
