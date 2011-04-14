from django import http
from django.conf import settings

from input import urlresolvers


def clean_url_prefixes(sender, **kwargs):
    """Wipe the URL prefixer(s) after each test."""
    urlresolvers.clean_url_prefixes()


def default_prefixer(sender, **kwargs):
    """Make sure each test starts with a default URL prefixer."""
    request = http.HttpRequest()
    request.META['SCRIPT_NAME'] = ''
    prefixer = urlresolvers.Prefixer(request)
    prefixer.locale = settings.LANGUAGE_CODE
    urlresolvers.set_url_prefix(prefixer)


# Register Django signals this app listens to.
try:
    import test_utils.signals
except ImportError:  # pragma: no cover
    pass
else:
    # Clean up URL prefix cache when a new test is invoked.
    test_utils.signals.pre_setup.connect(default_prefixer)
    test_utils.signals.post_teardown.connect(clean_url_prefixes)
