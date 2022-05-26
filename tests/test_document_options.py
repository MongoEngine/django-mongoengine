from django_mongoengine import Document, fields
from django_mongoengine.fields import ObjectIdField


class TestModel(Document):
    name = fields.StringField(max_length=100)


def test_get_field():
    f = TestModel._meta.get_field("id")
    assert isinstance(f, ObjectIdField)
