#!/usr/bin/env python
# coding=utf-8
from __future__ import absolute_import, division, print_function

from django.conf.urls import url
from django.views.decorators.cache import cache_page

from django.views.generic import TemplateView

from . import views

urlpatterns = [
    # TemplateView
    url(r'^template/no_template/$', TemplateView.as_view()),
    url(r'^template/simple/(?P<foo>\w+)/$',
     TemplateView.as_view(template_name='views/about.html')),
    url(r'^template/custom/(?P<foo>\w+)/$',
     views.CustomTemplateView.as_view(template_name='views/about.html')),
    url(r'^template/cached/(?P<foo>\w+)/$',
     cache_page(2.0)(TemplateView.as_view(template_name='views/about.html'))),

    # DetailView
    url(r'^detail/obj/$', views.ObjectDetail.as_view()),
    url(r'^detail/artist/(?P<pk>\d+)/$',
        views.ArtistDetail.as_view(),
        name="artist_detail"),
    url(r'^detail/author/(?P<pk>\d+)/$',
        views.AuthorDetail.as_view(),
        name="author_detail"),
    url(r'^detail/author/bycustompk/(?P<foo>\d+)/$',
     views.AuthorDetail.as_view(pk_url_kwarg='foo')),
    url(r'^detail/author/byslug/(?P<slug>[\w-]+)/$',
     views.AuthorDetail.as_view()),
    url(r'^detail/author/bycustomslug/(?P<foo>[\w-]+)/$',
     views.AuthorDetail.as_view(slug_url_kwarg='foo')),
    url(r'^detail/author/(?P<pk>\d+)/template_name_suffix/$',
     views.AuthorDetail.as_view(template_name_suffix='_view')),
    url(r'^detail/author/(?P<pk>\d+)/template_name/$',
     views.AuthorDetail.as_view(template_name='views/about.html')),
    url(r'^detail/author/(?P<pk>\d+)/context_object_name/$',
     views.AuthorDetail.as_view(context_object_name='thingy')),
    url(r'^detail/author/(?P<pk>\d+)/dupe_context_object_name/$',
     views.AuthorDetail.as_view(context_object_name='object')),
    url(r'^detail/page/(?P<pk>\d+)/field/$', views.PageDetail.as_view()),
    url(r'^detail/author/invalid/url/$', views.AuthorDetail.as_view()),
    url(r'^detail/author/invalid/qs/$',
     views.AuthorDetail.as_view(queryset=None)),

    # Create/UpdateView
    url(r'^edit/artists/create/$', views.ArtistCreate.as_view()),
    url(r'^edit/artists/(?P<pk>\d+)/update/$', views.ArtistUpdate.as_view()),
    url(r'^edit/authors/create/naive/$', views.NaiveAuthorCreate.as_view()),
    url(r'^edit/authors/create/redirect/$',
     views.NaiveAuthorCreate.as_view(success_url='/edit/authors/create/')),
    url(r'^edit/authors/create/interpolate_redirect/$',
     views.NaiveAuthorCreate.as_view(
         success_url='/edit/author/{id}/update/')),
    url(r'^edit/authors/create/$', views.AuthorCreate.as_view()),
    url(r'^edit/authors/create/special/$',
     views.SpecializedAuthorCreate.as_view()),
    url(r'^edit/author/(?P<pk>\d+)/update/naive/$',
     views.NaiveAuthorUpdate.as_view()),
    url(r'^edit/author/(?P<pk>\d+)/update/redirect/$',
     views.NaiveAuthorUpdate.as_view(success_url='/edit/authors/create/')),
    url(r'^edit/author/(?P<pk>\d+)/update/interpolate_redirect/$',
     views.NaiveAuthorUpdate.as_view(
         success_url='/edit/author/{id}/update/')),
    url(r'^edit/author/(?P<pk>\d+)/update/$', views.AuthorUpdate.as_view()),
    url(r'^edit/author/update/$', views.OneAuthorUpdate.as_view()),
    url(r'^edit/author/(?P<pk>\d+)/update/special/$',
     views.SpecializedAuthorUpdate.as_view()),
    url(r'^edit/author/(?P<pk>\d+)/delete/naive/$',
     views.NaiveAuthorDelete.as_view()),
    url(r'^edit/author/(?P<pk>\d+)/delete/redirect/$',
     views.NaiveAuthorDelete.as_view(success_url='/edit/authors/create/')),
    url(r'^edit/author/(?P<pk>\d+)/delete/$', views.AuthorDelete.as_view()),
    url(r'^edit/author/(?P<pk>\d+)/delete/special/$',
     views.SpecializedAuthorDelete.as_view()),

    # ListView
    url(r'^list/dict/$', views.DictList.as_view()),
    url(r'^list/dict/paginated/$', views.DictList.as_view(paginate_by=1)),
    url(r'^list/artists/$',
        views.ArtistList.as_view(),
        name="artists_list"),
    url(r'^list/authors/$',
        views.AuthorList.as_view(),
        name="authors_list"),
    url(r'^list/authors/paginated/$', views.AuthorList.as_view(paginate_by=30)),
    url(r'^list/authors/paginated/(?P<page>\d+)/$',
     views.AuthorList.as_view(paginate_by=30)),
    url(r'^list/authors/notempty/$', views.AuthorList.as_view(allow_empty=False)),
    url(r'^list/authors/template_name/$',
     views.AuthorList.as_view(template_name='views/list.html')),
    url(r'^list/authors/template_name_suffix/$',
     views.AuthorList.as_view(template_name_suffix='_objects')),
    url(r'^list/authors/context_object_name/$',
     views.AuthorList.as_view(context_object_name='author_list')),
    url(r'^list/authors/dupe_context_object_name/$',
     views.AuthorList.as_view(context_object_name='object_list')),
    url(r'^list/authors/invalid/$', views.AuthorList.as_view(queryset=None)),
    url(r'^list/authors/paginated/custom_class/$',
     views.AuthorList.as_view(paginate_by=5,
                              paginator_class=views.CustomPaginator)),
    url(r'^list/authors/paginated/custom_constructor/$',
     views.AuthorListCustomPaginator.as_view()),
]
