from django_mongoengine.forms import EmbeddedDocumentForm

from tumblelog.models import BlogPost, Comment


class CommentForm(EmbeddedDocumentForm):

    class Meta:
        document = Comment
        embedded_field_name = 'comments'
        exclude = ('created_at',)
