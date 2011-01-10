from django.conf.urls.defaults import url, patterns, include
from django.conf import settings
from django.contrib import admin
from django.http import HttpResponsePermanentRedirect as Redirect

import jingo

from input.urlresolvers import reverse


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

    (r'^robots\.txt$', jingo.render, {'template': 'robots.txt',
                                      'mimetype': 'text/plain'}),

    # Redirects for deprecated URLs.
    url(r'^feedback/?', lambda r: Redirect(reverse('feedback.release_feedback'))),
    url(r'^thanks/?', lambda r: Redirect(reverse('feedback.thanks'))),
    url(r'^download/?', lambda r: Redirect(reverse('feedback.need_beta'))),
    url(r'^search/?$', lambda r: Redirect(reverse('search'))),
    url(r'^search/atom/?$', lambda r: Redirect(reverse('search.feed'))),
    url(r'^themes/?$', lambda r: Redirect(reverse('themes'))),
    url(r'^themes/(?P<theme_id>\d+)/?$', lambda r, theme_id: Redirect(
            reverse('theme', args=[theme_id]))),
    url(r'^sites/?', lambda r: Redirect(reverse('website_issues'))),
    url(r'^site/(?P<protocol>\w+)/(?P<url_>.+)$',
        lambda r, protocol, url_: Redirect(reverse(
            'single_site', args=[protocol, url_]))),
    url(r'^sites/theme/(?P<theme_id>\d+)$',
        lambda r, theme_id: Redirect(reverse(
            'site_theme', args=[theme_id]))),
)

if settings.DEBUG:
    # Remove leading and trailing slashes so the regex matches.
    media_url = settings.MEDIA_URL.strip('/')
    urlpatterns += patterns('',
        (r'^%s/(?P<path>.*)$' % media_url, 'django.views.static.serve',
         {'document_root': settings.MEDIA_ROOT}),
    )
