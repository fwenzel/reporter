from django.conf.urls.defaults import *
from django.contrib import admin

import jingo


def _error_page(request, status):
    """Render error pages with jinja2."""
    return jingo.render(request, '%d.html' % status, status=status)
handler404 = lambda r: _error_page(r, 404)
handler500 = lambda r: _error_page(r, 500)


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
