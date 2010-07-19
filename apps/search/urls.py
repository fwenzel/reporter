from django.conf.urls.defaults import patterns, url

import views

urlpatterns = patterns('',
    url(r'^atom/$', views.SearchFeed(), name='search.feed'),
    url(r'^$', views.index, name='search'),
)
