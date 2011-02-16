from functools import wraps

from django.conf import settings
from django.http import HttpRequest
from django.test.client import Client

import jingo
import test_utils

from input import urlresolvers


FX_UA = ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; '
         'en-US; rv:1.9.2.3) Gecko/20100401 Firefox/%s')
FENNEC_UA = ('Mozilla/5.0 (X11; U; Linux armv6l; fr; rv:1.9.1b1pre) Gecko/'
             '20081005220218 Gecko/2008052201 Fennec/0.9pre')


def enforce_ua(f):
    """Decorator to switch on UA enforcement for the duration of a test."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        old_enforce_setting = settings.ENFORCE_USER_AGENT
        try:
            settings.ENFORCE_USER_AGENT = True
            f(*args, **kwargs)
        finally:
            settings.ENFORCE_USER_AGENT = old_enforce_setting
    return wrapped


def render(s, context={}):
    """Render a Jinja2 template fragment."""
    t = jingo.env.from_string(s)
    return t.render(**context)


class InputTestCase(test_utils.TestCase):
    """TestCase containing some useful shortcuts."""

    def setUp(self):
        super(InputTestCase, self).setUp()
        self.fxclient = Client(False, HTTP_USER_AGENT=(FX_UA % '4.0'))
        self.mclient = Client(False, HTTP_USER_AGENT=FENNEC_UA)
        self.factory = test_utils.RequestFactory()


class ViewTestCase(InputTestCase):
    def setUp(self):
        """Set up URL prefixer."""
        super(ViewTestCase, self).setUp()
        urlresolvers.set_url_prefix(urlresolvers.Prefixer(HttpRequest()))
