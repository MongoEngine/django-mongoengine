from django.http import HttpResponseRedirect

from django_mongoengine.views import (CreateView, UpdateView,
                                      DeleteView, ListView, DetailView)

from tumblelog.models import Post
from tumblelog.forms import PostForm, CommentForm


class PostIndexView(ListView):
    document = Post


class PostDetailView(DetailView):
    document = Post


class AddPostView(CreateView):
    document = Post
    success_url = '/'
    form_exclude = ('created_at', )
    form_class = PostForm


class DeletePostView(DeleteView):
    document = Post
    success_url = '/'


class UpdatePostView(UpdateView):
    document = Post
    form_class = PostForm


# class PostDetailView(DetailView):
#     methods = ['get', 'post']

#     document =

#     def get(self, request, *args, **kwargs):
#         self.object = self.get_object()
#         form = CommentForm(object=self.object)
#         context = self.get_context_data(object=self.object, form=form)
#         return self.render_to_response(context)

#     def post(self, request, *args, **kwargs):
#         self.object = self.get_object()
#         form = CommentForm(object=self.object, data=request.POST)

#         if form.is_valid():
#             form.save()
#             return HttpResponseRedirect(self.object.get_absolute_url())

#         context = self.get_context_data(object=self.object, form=form)
#         return self.render_to_response(context)

