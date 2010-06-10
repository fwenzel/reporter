from django.conf.urls.defaults import *
from django.contrib import admin

import jingo

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^$', 'dashboard.views.dashboard', name='dashboard'),

    ('', include('feedback.urls')),
    (r'^dashboard/', include('dashboard.urls')),
    (r'^search/', include('search.urls')),
    (r'^admin/', include(admin.site.urls)),

    (r'^robots\.txt$', jingo.render, {'template': 'robots.txt',
                                      'mimetype': 'text/plain'}),
)
