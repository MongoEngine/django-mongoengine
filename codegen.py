def generate_fields():
    """
    Typing support cannot handle monkey-patching at runtime, so we need to generate fields explicitly.
    """
    from mongoengine import fields
    from django_mongoengine.fields import djangoflavor as mixins

    fields_code = str(_fields)
    for fname in fields.__all__:
        mixin_name = fname if hasattr(mixins, fname) else "DjangoField"
        fields_code += f"class {fname}(_mixins.{mixin_name}, _fields.{fname}):\n    pass\n"

    return fields_code


_fields = """
from mongoengine import fields as _fields
from . import djangoflavor as _mixins
from django_mongoengine.utils.monkey import patch_mongoengine_field

for f in ["StringField", "ObjectIdField"]:
    patch_mongoengine_field(f)

"""

if __name__ == "__main__":
    fname = "django_mongoengine/fields/__init__.py"
    # This content required, because otherwise mixins import does not work.
    open(fname, "w").write("from mongoengine.fields import *")
    content = generate_fields()
    open(fname, "w").write(content)
