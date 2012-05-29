from django.core.urlresolvers import reverse

from django_mongoengine import Document
from django_mongoengine import fields

import datetime


class Post(Document):
    created_at = fields.DateTimeField(default=datetime.datetime.now, required=True)
    title = fields.StringField(max_length=255, required=True)
    slug = fields.StringField(max_length=255, required=True, primary_key=True)
    comments = fields.ListField(fields.EmbeddedDocumentField('Comment'))

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
    body = fields.StringField(required=True)


class Video(Post):
    embed_code = fields.StringField(required=True)


class Image(Post):
    image_url = fields.StringField(required=True, max_length=255)


class Quote(Post):
    body = fields.StringField(required=True)
    author = fields.StringField(verbose_name="Author Name", required=True, max_length=255)


class Comment(fields.EmbeddedDocument):
    created_at = fields.DateTimeField(default=datetime.datetime.now, required=True)
    author = fields.StringField(verbose_name="Name", max_length=255, required=True)
    body = fields.StringField(verbose_name="Comment", required=True)
