from django.conf.urls import patterns, include, url

from tumblelog.views import (PostIndexView, AddPostView, PostDetailView,
                             UpdatePostView, DeletePostView, ImageFileView)

from django_mongoengine import mongo_admin

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
    url(r'^admin/', include(mongo_admin.site.urls)),
    url(r'^image-file/(?P<slug>[a-zA-Z0-9-]+)/', ImageFileView.as_view(),
            name="image_file"),
    url(r'^(?P<slug>[a-zA-Z0-9-]+)/', include(post_patterns))
)
