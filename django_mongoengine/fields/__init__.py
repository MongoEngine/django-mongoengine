from mongoengine import fields as _fields
from . import djangoflavor as _mixins
from django_mongoengine.utils.monkey import patch_mongoengine_field

for f in ["StringField", "ObjectIdField"]:
    patch_mongoengine_field(f)


class StringField(_mixins.StringField, _fields.StringField):
    pass


class URLField(_mixins.URLField, _fields.URLField):
    pass


class EmailField(_mixins.EmailField, _fields.EmailField):
    pass


class IntField(_mixins.IntField, _fields.IntField):
    pass


class LongField(_mixins.DjangoField, _fields.LongField):
    pass


class FloatField(_mixins.FloatField, _fields.FloatField):
    pass


class DecimalField(_mixins.DecimalField, _fields.DecimalField):
    pass


class BooleanField(_mixins.BooleanField, _fields.BooleanField):
    pass


class DateTimeField(_mixins.DateTimeField, _fields.DateTimeField):
    pass


class DateField(_mixins.DjangoField, _fields.DateField):
    pass


class ComplexDateTimeField(_mixins.DjangoField, _fields.ComplexDateTimeField):
    pass


class EmbeddedDocumentField(_mixins.EmbeddedDocumentField, _fields.EmbeddedDocumentField):
    pass


class ObjectIdField(_mixins.DjangoField, _fields.ObjectIdField):
    pass


class GenericEmbeddedDocumentField(_mixins.DjangoField, _fields.GenericEmbeddedDocumentField):
    pass


class DynamicField(_mixins.DjangoField, _fields.DynamicField):
    pass


class ListField(_mixins.ListField, _fields.ListField):
    pass


class SortedListField(_mixins.DjangoField, _fields.SortedListField):
    pass


class EmbeddedDocumentListField(_mixins.DjangoField, _fields.EmbeddedDocumentListField):
    pass


class DictField(_mixins.DictField, _fields.DictField):
    pass


class MapField(_mixins.DjangoField, _fields.MapField):
    pass


class ReferenceField(_mixins.ReferenceField, _fields.ReferenceField):
    pass


class CachedReferenceField(_mixins.DjangoField, _fields.CachedReferenceField):
    pass


class LazyReferenceField(_mixins.DjangoField, _fields.LazyReferenceField):
    pass


class GenericLazyReferenceField(_mixins.DjangoField, _fields.GenericLazyReferenceField):
    pass


class GenericReferenceField(_mixins.DjangoField, _fields.GenericReferenceField):
    pass


class BinaryField(_mixins.DjangoField, _fields.BinaryField):
    pass


class GridFSError(_mixins.DjangoField, _fields.GridFSError):
    pass


class GridFSProxy(_mixins.DjangoField, _fields.GridFSProxy):
    pass


class FileField(_mixins.FileField, _fields.FileField):
    pass


class ImageGridFsProxy(_mixins.DjangoField, _fields.ImageGridFsProxy):
    pass


class ImproperlyConfigured(_mixins.ImproperlyConfigured, _fields.ImproperlyConfigured):
    pass


class ImageField(_mixins.ImageField, _fields.ImageField):
    pass


class GeoPointField(_mixins.DjangoField, _fields.GeoPointField):
    pass


class PointField(_mixins.DjangoField, _fields.PointField):
    pass


class LineStringField(_mixins.DjangoField, _fields.LineStringField):
    pass


class PolygonField(_mixins.DjangoField, _fields.PolygonField):
    pass


class SequenceField(_mixins.DjangoField, _fields.SequenceField):
    pass


class UUIDField(_mixins.DjangoField, _fields.UUIDField):
    pass


class EnumField(_mixins.DjangoField, _fields.EnumField):
    pass


class MultiPointField(_mixins.DjangoField, _fields.MultiPointField):
    pass


class MultiLineStringField(_mixins.DjangoField, _fields.MultiLineStringField):
    pass


class MultiPolygonField(_mixins.DjangoField, _fields.MultiPolygonField):
    pass


class GeoJsonBaseField(_mixins.DjangoField, _fields.GeoJsonBaseField):
    pass


class Decimal128Field(_mixins.DjangoField, _fields.Decimal128Field):
    pass
