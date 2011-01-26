from django.conf.urls.defaults import url, patterns, include
from django.conf import settings
from django.contrib import admin

import jingo


def _error_page(request, status):
    """Render error pages with jinja2."""
    return jingo.render(request, '%d.html' % status, status=status)
handler404 = lambda r: _error_page(r, 404)
handler500 = lambda r: _error_page(r, 500)


admin.autodiscover()

urlpatterns = patterns('',
    ('', include('dashboard.urls')),
    ('', include('feedback.urls')),
    ('', include('website_issues.urls')),
    ('', include('search.urls')),
    ('', include('themes.urls')),

    (r'^admin/', include('myadmin.urls')),

    url(r'^about/?$', jingo.render, {'template': 'about.html'},
        name='about'),
    (r'^robots\.txt$', jingo.render, {'template': 'robots.txt',
                                      'mimetype': 'text/plain'}),
)

if settings.DEBUG:
    # Remove leading and trailing slashes so the regex matches.
    media_url = settings.MEDIA_URL.strip('/')
    urlpatterns += patterns('',
        (r'^%s/(?P<path>.*)$' % media_url, 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT}),
    )
