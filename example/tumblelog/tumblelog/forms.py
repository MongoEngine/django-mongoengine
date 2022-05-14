from tumblelog import models

from django_mongoengine import forms


class CommentForm(forms.EmbeddedDocumentForm):
    class Meta:
        document = models.Comment
        embedded_field = 'comments'
        exclude = ('created_at',)
