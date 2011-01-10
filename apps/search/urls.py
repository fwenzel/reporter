from django.conf.urls.defaults import patterns, url

from search import views


urlpatterns = patterns('',
    url(r'^beta/search/?$', views.index, name='search'),
    url(r'^beta/search/atom/?$', views.SearchFeed(), name='search.feed'),
)
