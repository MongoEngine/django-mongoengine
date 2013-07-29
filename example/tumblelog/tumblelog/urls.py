from django.conf.urls import patterns, include, url

from tumblelog.views import (PostIndexView, AddPostView, PostDetailView,
                             UpdatePostView, DeletePostView, ImageFileView)

# # Enable admin
from django.contrib import admin
admin.autodiscover()

from django_mongoengine.admin import site

post_patterns = patterns('',
    url(r'^$', PostDetailView.as_view(), name="post"),
    url(r'^edit/$', UpdatePostView.as_view(), name="post_update"),
    url(r'^delete/$', DeletePostView.as_view(), name="post_delete")
)


urlpatterns = patterns('',
    url(r'^$', PostIndexView.as_view(), name="post_index"),
    url(r'^new/$', AddPostView.as_view(), name="post_new"),
    url(r'^new/(?P<post_type>(post|video|image|quote|music))/$',
            AddPostView.as_view(), name="post_new"),
    url(r'^admin/', include(site.urls)),
    url(r'^image-file/(?P<slug>[a-zA-Z0-9-]+)/', ImageFileView.as_view(),
            name="image_file"),
    url(r'^(?P<slug>[a-zA-Z0-9-]+)/', include(post_patterns))
)
