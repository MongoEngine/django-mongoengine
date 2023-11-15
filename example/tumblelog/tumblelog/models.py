from django.urls import reverse

import datetime

from django_mongoengine import Document, EmbeddedDocument, fields


class Comment(EmbeddedDocument):
    created_at = fields.DateTimeField(
        default=datetime.datetime.now,
        editable=False,
    )
    author = fields.StringField(verbose_name="Name", max_length=255, required=True)
    email = fields.EmailField(verbose_name="Email", required=True)
    body = fields.StringField(verbose_name="Comment", required=True)


class Post(Document):
    created_at = fields.DateTimeField(
        default=datetime.datetime.now,
        editable=False,
    )
    title = fields.StringField(max_length=255, required=True)
    slug = fields.StringField(max_length=255, primary_key=True, required=True)
    comments = fields.ListField(
        fields.EmbeddedDocumentField(Comment, required=True),
        default=[],
    )
    strings = fields.ListField(
        fields.StringField(required=True),
        default=[],
    )

    def get_absolute_url(self):
        return reverse("post", kwargs={"slug": self.slug})

    def __str__(self):
        return self.title

    @property
    def post_type(self):
        return self.__class__.__name__

    meta = {
        "indexes": ["-created_at", "slug"],
        "ordering": ["-created_at"],
        "allow_inheritance": True,
    }


class BlogPost(Post):
    body = fields.StringField(required=True)


class Video(Post):
    embed_code = fields.StringField(required=True)


class Image(Post):
    image = fields.ImageField(required=True)


class Quote(Post):
    body = fields.StringField(required=True)
    author = fields.StringField(verbose_name="Author Name", max_length=255, required=True)


class Music(Post):
    url = fields.StringField(max_length=100, verbose_name="Music Url", required=True)
    music_parameters = fields.DictField(verbose_name="Music Parameters", required=True)
