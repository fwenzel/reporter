from django.conf.urls.defaults import patterns, url, include
from django.contrib import admin

from myadmin import views

urlpatterns = patterns('',
    # Input stuff.
    url('^recluster/?$', views.recluster, name='myadmin.recluster'),
    url('^export_tsv/?$', views.export_tsv, name='myadmin.export_tsv'),
    url('^settings/?$', views.settings, name='myadmin.settings'),

    # The Django admin.
    url('^', include(admin.site.urls)),
)

