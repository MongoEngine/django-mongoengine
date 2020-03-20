from django_mongoengine import forms

from tumblelog import models


class CommentForm(forms.EmbeddedDocumentForm):

    class Meta:
        document = models.Comment
        embedded_field = 'comments'
        exclude = ('created_at',)
