from django.http import HttpResponseRedirect

from django_mongoengine.forms.documents import documentform_factory
from django_mongoengine.views import (CreateView, UpdateView,
                                      DeleteView, ListView, DetailView,
                                      EmbeddedDetailView)

from tumblelog.models import Post, BlogPost, Video, Image, Quote
from tumblelog.forms import CommentForm


class PostIndexView(ListView):
    document = Post
    context_object_name = 'posts_list'


class PostDetailView(EmbeddedDetailView):
    document = Post
    context_object_name = 'post'
    embedded_context_name = 'form'
    embedded_form_class = CommentForm
    success_message = "Comment Posted!"


class AddPostView(CreateView):
    success_url = '/'
    doc_map = {'post': BlogPost, 'video': Video, 'image': Image, 'quote': Quote}
    success_message = "Post Added!"
    form_exclude = ('created_at', 'comments')

    @property
    def document(self):
        post_type = self.kwargs.get('post_type', 'post')
        return self.doc_map.get(post_type)


class DeletePostView(DeleteView):
    document = Post
    success_url = '/'


class UpdatePostView(UpdateView):
    document = Post
    form_exclude = ('created_at', 'comments',)