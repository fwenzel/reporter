from functools import wraps

from django.conf import settings
from django.utils.hashcompat import md5_constructor

from view_cache_utils import cache_page_with_prefix


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
