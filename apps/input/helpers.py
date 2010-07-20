import cgi
import datetime
import urllib
import urlparse

from django.conf import settings
from django.template import defaultfilters
from django.utils import translation

from babel import Locale
from babel.dates import format_datetime
from babel.support import Format
from jingo import register
import jinja2
import pytz

import utils
from .urlresolvers import reverse


# Yanking filters from Django.
register.filter(defaultfilters.iriencode)


def _get_format():
    lang = translation.get_language()
    locale = Locale(translation.to_locale(lang))
    return Format(locale)


@register.filter
def numberfmt(num, format=None):
    return _get_format().decimal(num, format)


@register.filter
def isotime(t):
    """Date/Time format according to ISO 8601"""
    if not hasattr(t, 'tzinfo'):
        return
    return _append_tz(t).astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _append_tz(t):
    tz = pytz.timezone(settings.TIME_ZONE)
    return tz.localize(t)


@register.filter
def babel_date(t, format='medium'):
    return _get_format().date(t, format=format)


@register.filter
def babel_datetime(t, format='medium'):
    return _get_format().datetime(t, format=format)


@register.function
def url(viewname, *args, **kwargs):
    """Helper for Django's ``reverse`` in templates."""
    return reverse(viewname, args=args, kwargs=kwargs)


@register.filter
def urlparams(url_, hash=None, **query):
    """
Add a fragment and/or query paramaters to a URL.

New query params will be appended to exising parameters, except duplicate
names, which will be replaced.
"""
    url_ = urlparse.urlparse(url_)
    fragment = hash if hash is not None else url_.fragment

    items = []
    if url_.query:
        for k, v in cgi.parse_qsl(url_.query):
            items.append((k, v))
    for k, v in query.items():
        items.append((k, v))

    items = [(k, unicode(v).encode('raw_unicode_escape')) for
             k, v in items if v is not None]

    query_string = _urlencode(items)

    new = urlparse.ParseResult(url_.scheme, url_.netloc, url_.path,
                               url_.params, query_string, fragment)
    return jinja2.Markup(new.geturl())


def _urlencode(items):
    """A Unicode-safe URLencoder."""
    try:
        return urllib.urlencode(items)
    except UnicodeEncodeError:
        return urllib.urlencode([(k, smart_str(v)) for k, v in items])
