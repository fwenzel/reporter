from django.conf.urls.defaults import patterns, url

from search import views


urlpatterns = patterns('',
    url(r'^search/?$', views.index, name='search'),
    url(r'^search/atom/?$', views.SearchFeed(), name='search.feed'),
)
