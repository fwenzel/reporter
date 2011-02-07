from functools import wraps
import re
import urllib

from django.conf import settings
from django.contrib.sites.models import Site
from django.http import HttpResponsePermanentRedirect
from django.utils.hashcompat import md5_constructor

from view_cache_utils import cache_page_with_prefix


# Known mobile device patterns. Excludes iPad because it's big enough to show
# the desktop dashboard.
MOBILE_DEVICE_PATTERN = re.compile(
    r'^Mozilla.*(Fennec|Android|Maemo|iPhone|iPod)')


def cache_page(cache_timeout=None, use_get=False, **kwargs):
    """
    Cache an entire page with a cache prefix based on the Site ID and
    (optionally) the GET parameters.
    """
    # If the first argument is a callable, we've used the decorator without
    # args.
    if callable(cache_timeout):
        f = cache_timeout
        return cache_page()(f)

    if cache_timeout is None:
        cache_timeout = settings.CACHE_DEFAULT_PERIOD

    def key_prefix(request):
        prefix = '%ss%d:' % (settings.CACHE_PREFIX, settings.SITE_ID)
        if use_get:
            prefix += md5_constructor(str(request.GET)).hexdigest()
        return prefix

    def wrap(f):
        @wraps(f)
        @cache_page_with_prefix(cache_timeout, key_prefix)
        def cached_view(request, *args, **kwargs):
            return f(request, *args, **kwargs)
        return cached_view
    return wrap


def forward_mobile(f):
    """Forward mobile requests to the same path on the mobile domain."""

    @wraps(f)
    def wrapped(request, *args, **kwargs):
        if (settings.SITE_ID == settings.DESKTOP_SITE_ID and
            MOBILE_DEVICE_PATTERN.search(
                request.META.get('HTTP_USER_AGENT', ''))):
            mobile_site = Site.objects.get(id=settings.MOBILE_SITE_ID)
            target = '%s://%s%s' % ('https' if request.is_secure() else 'http',
                                    mobile_site.domain, request.path)
            if request.GET:
                target = '%s?%s' % (target, urllib.urlencode(request.GET))

            response = HttpResponsePermanentRedirect(target)
            response['Vary'] = 'User-Agent'
            return response

        return f(request, *args, **kwargs)

    return wrapped


# Not quite a decorator:
def negotiate(release, beta):
    """
    If
        /beta/foo
        /release/foo
    exist

    you can create a urls.py that points 'foo' to views.foo
    in views.py:

        foo = negotiate(beta=beta_foo, release=release_foo,
                        nightly=nightly_foo)

    Will then serve up the correct view based on your request.
    """
    def negotiated(request, *args, **kwargs):
        if request.channel == 'beta':
            return beta(request, *args, **kwargs)
        else:
            return release(request, *args, **kwargs)
    return negotiated
