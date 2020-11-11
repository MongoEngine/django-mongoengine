from bson import ObjectId
from mongoengine.errors import FieldDoesNotExist


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
        field = self._meta.get_field(field_name)
    except FieldDoesNotExist:
        return getattr(self, field_name)
    value = field.to_mongo(getattr(self, field.name))
    if isinstance(value, ObjectId):
        return str(value)
    return value
