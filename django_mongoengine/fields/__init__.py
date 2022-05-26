from . import djangoflavor


def init_module():
    """
    Create classes with Django-flavor mixins,
    use DjangoField mixin as default
    """
    import sys

    from mongoengine import fields

    current_module = sys.modules[__name__]
    current_module.__all__ = fields.__all__

    for name in fields.__all__:
        fieldcls = getattr(fields, name)
        mixin = getattr(djangoflavor, name, djangoflavor.DjangoField)
        setattr(
            current_module,
            name,
            type(name, (mixin, fieldcls), {}),
        )


def patch_mongoengine_field(field_name):
    """
    patch mongoengine.[field_name] for comparison support
    becouse it's required in django.forms.models.fields_for_model
    importing using mongoengine internal import cache
    """
    from mongoengine import common

    field = common._import_class(field_name)
    for k in ["__eq__", "__lt__", "__hash__", "attname", "get_internal_type"]:
        if k not in field.__dict__:
            setattr(field, k, djangoflavor.DjangoField.__dict__[k])


init_module()

for f in ["StringField", "ObjectIdField"]:
    patch_mongoengine_field(f)
