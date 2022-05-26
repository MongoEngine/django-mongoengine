from django_mongoengine.fields import ObjectIdField

from .views.models import City


def test_id_field_uses_custom_class():
    f = City._meta.get_field("id")
    assert isinstance(f, ObjectIdField)
