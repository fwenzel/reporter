from django.conf import settings
from django import http

from product_details import firefox_versions, mobile_details
from . import FIREFOX, MOBILE
from .utils import ua_parse
from .version_compare import version_int


LATEST_BETAS = {
    FIREFOX: firefox_versions['LATEST_FIREFOX_DEVEL_VERSION'],
    MOBILE: mobile_details['beta_version'],
}


def enforce_user_agent(f):
    """
    View decorator enforcing feedback from the latest beta users only.

    Can be disabled with settings.ENFORCE_USER_AGENT = False.
    """
    def wrapped(request, *args, **kwargs):
        if request.method != 'GET' or not settings.ENFORCE_USER_AGENT:
            return f(request, *args, **kwargs)

        # user agent GET parameter must be set and parseable
        ua = request.GET.get('ua', None)
        parsed = ua_parse(ua)
        if not parsed:
            return http.HttpResponseRedirect(settings.URL_BETA)

        # compare to latest beta
        ref_version = LATEST_BETAS[parsed['browser']]
        if (version_int(ref_version) != version_int(parsed['version'])):
            return http.HttpResponseRedirect(settings.URL_BETA)

        # if we made it here, it's a latest beta user
        return f(request, *args, **kwargs)

    return wrapped
