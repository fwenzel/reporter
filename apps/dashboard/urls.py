from django.conf.urls.defaults import patterns, url
from django.http import HttpResponsePermanentRedirect

from input.urlresolvers import reverse


urlpatterns = patterns('dashboard.views',
    # TODO Do some UA detection to forward to the right dashboard?
    url(r'^$', lambda r: HttpResponsePermanentRedirect(reverse(
        'dashboard'))),

    # TODO Split this up into beta, release dashboards.
    url(r'^beta/$', 'dashboard', name='dashboard'),
)
