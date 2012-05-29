from django.conf.urls.defaults import patterns, include, url

from tumblelog.views import PostIndexView, AddPostView, PostDetailView, UpdatePostView, DeletePostView

# # Enable admin
# from django.contrib import admin
# admin.autodiscover()

post_patterns  = patterns('',
    url(r'^$', PostDetailView.as_view(), name="post"),
    url(r'^edit/$', UpdatePostView.as_view(), name="post_update"),
    url(r'^delete/$', DeletePostView.as_view(), name="post_delete")
)


urlpatterns = patterns('',
    url(r'^$', PostIndexView.as_view(), name="post_index"),
    url(r'^new/$', AddPostView.as_view(), name="post_new"),
    url(r'^new/(?P<post_type>(post|video|image|quote))/$', AddPostView.as_view(), name="post_new"),
    url(r'^(?P<slug>[a-zA-Z0-9-]+)/', include(post_patterns))
)