from bson.objectid import ObjectId
from django.urls import reverse

from django_mongoengine import Document, fields


def object_id() -> str:
    return str(ObjectId())


class Artist(Document):
    id = fields.StringField(primary_key=True, default=object_id)
    name = fields.StringField(max_length=100, required=True)

    class Meta:
        ordering = (["name"],)
        verbose_name = ("professional artist",)
        verbose_name_plural = "professional artists"

    def __str__(self):
        return self.name or ""

    def get_absolute_url(self):
        return reverse("artist_detail", args=(self.id,))


class Author(Document):
    id = fields.StringField(primary_key=True, default=object_id)
    name = fields.StringField(max_length=100, required=True)
    slug = fields.StringField(required=True)

    _meta = {"ordering": ["name"], "exclude": "id"}

    def __str__(self):
        return self.name or ""


class Book(Document):
    id = fields.StringField(primary_key=True, default=object_id)
    name = fields.StringField(max_length=300, required=True)
    slug = fields.StringField(required=True)
    pages = fields.IntField(required=True)
    authors = fields.ListField(fields.ReferenceField(Author, required=True))
    pubdate = fields.DateTimeField(required=True)

    _meta = {"ordering": ["-pubdate"]}

    def __str__(self):
        return self.name or ""


class Page(Document):
    id = fields.StringField(primary_key=True, default=object_id)
    content = fields.StringField(required=True)
    template = fields.StringField(max_length=300, required=True)


class City(Document):
    name = fields.StringField(max_length=100, required=True)
