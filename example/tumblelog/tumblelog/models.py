try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse

from django_mongoengine import Document, EmbeddedDocument
from django_mongoengine import fields

import datetime


class Comment(EmbeddedDocument):
    created_at = fields.DateTimeField(
        default=datetime.datetime.now, editable=False,
    )
    author = fields.StringField(verbose_name="Name", max_length=255)
    email  = fields.EmailField(verbose_name="Email", blank=True)
    body = fields.StringField(verbose_name="Comment")


class Post(Document):
    created_at = fields.DateTimeField(
        default=datetime.datetime.now, editable=False,
    )
    title = fields.StringField(max_length=255)
    slug = fields.StringField(max_length=255, primary_key=True)
    comments = fields.ListField(
        fields.EmbeddedDocumentField('Comment'),
        default=[],
        blank=True,
    )

    def get_absolute_url(self):
        return reverse('post', kwargs={"slug": self.slug})

    def __unicode__(self):
        return self.title

    @property
    def post_type(self):
        return self.__class__.__name__

    meta = {
        'indexes': ['-created_at', 'slug'],
        'ordering': ['-created_at'],
        'allow_inheritance': True
    }


class BlogPost(Post):
    body = fields.StringField()


class Video(Post):
    embed_code = fields.StringField()


class Image(Post):
    image = fields.ImageField()


class Quote(Post):
    body = fields.StringField()
    author = fields.StringField(verbose_name="Author Name", max_length=255)


class Music(Post):
    url = fields.StringField(max_length=100, verbose_name="Music Url")
    music_parameters = fields.DictField(verbose_name="Music Parameters")
