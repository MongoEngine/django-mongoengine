from django_mongoengine import Document, fields
from django_mongoengine.fields import ObjectIdField


class SomeModel(Document):
    name = fields.StringField(max_length=100)


def test_id_field_uses_custom_class():
    f = SomeModel._meta.get_field("id")
    assert isinstance(f, ObjectIdField)
