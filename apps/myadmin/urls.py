from django.conf.urls.defaults import patterns, url, include
from django.contrib import admin

from myadmin import views

urlpatterns = patterns('',
    # Input stuff.
    url('^recluster', views.recluster, name='myadmin.recluster'),

    # The Django admin.
    url('^', include(admin.site.urls)),
)

