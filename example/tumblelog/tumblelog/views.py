from django.http import HttpResponse
from django.views.generic import View

from django_mongoengine.forms.fields import DictField
from django_mongoengine.views import (
    CreateView, UpdateView,
    DeleteView, ListView,
    DetailView,
    EmbeddedDetailView,
)

from tumblelog.models import Post, BlogPost, Video, Image, Quote, Music
from tumblelog import forms


class PostIndexView(ListView):
    document = Post
    context_object_name = 'posts_list'
    paginate_by = 5


class PostDetailView(EmbeddedDetailView):
    document = Post
    template_name = "_details.html"
    context_object_name = 'post'
    embedded_context_name = 'form'
    embedded_form_class = forms.CommentForm
    success_message = "Comment Posted!"


class AddPostView(CreateView):
    success_url = '/'
    template_name = "_forms.html"
    doc_map = {'post': BlogPost, 'video': Video, 'image': Image, 'quote': Quote, 'music': Music}
    success_message = "Post Added!"
    fields = "__all__"

    @property
    def document(self):
        post_type = self.kwargs.get('post_type', 'post')
        return self.doc_map.get(post_type)

    def get_form(self, form_class=None):
        form = super(AddPostView, self).get_form(form_class)
        music_parameters = form.fields.get('music_parameters', None)
        if music_parameters is not None:
            schema = {
                'Artist': '',
                'Title': '',
                'Album': '',
                'Genre': '',
                'Label': '',
                'Release dates': {
                    'UK': '',
                    'US': '',
                    'FR': ''
                }
            }
            music_parameters = DictField(initial=schema, flags=['FORCE_SCHEMA'])
            form.fields['music_parameters'] = music_parameters
        return form


class DeletePostView(DeleteView):
    context_object_name = 'post'
    document = Post
    success_url = '/'
    template_name = "_delete.html"


class UpdatePostView(UpdateView):
    document = Post
    template_name = "_forms.html"
    fields = "__all__"

    def get_form_class(self):
        from django_mongoengine.forms.documents import documentform_factory
        return documentform_factory(self.object.__class__, fields=self.fields)


class ImageFileView(DetailView):
    document = Image

    def get(self, request, *args, **kwargs):
        image = self.get_object().image
        return HttpResponse(
            image.read(),
            content_type='image/%s' % image.format.lower(),
        )


class TestSessionView(View):
    def get(self, request, *args, **kwargs):
        test_data = request.session.get('test', None)
        request.session['test'] = 'abc123'
        return HttpResponse('test=%s' % test_data)
