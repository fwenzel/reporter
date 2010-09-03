import cgi
import datetime
import urlparse

from django.conf import settings
from django.template import defaultfilters
from django.utils import translation
from django.utils.encoding import smart_str
from django.utils.http import urlencode

from babel import Locale
from babel.dates import format_datetime
from babel.support import Format
from jingo import register
import jinja2
import pytz

import utils
from .urlresolvers import reverse
from themes.helpers import new_context

# Yanking filters from Django.
register.filter(defaultfilters.iriencode)
register.filter(defaultfilters.timesince)


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
    url = urlparse.urlparse(url_)
    fragment = hash if hash is not None else url.fragment

    # Use dict(parse_qsl) so we don't get lists of values.
    q = url.query
    query_dict = dict(urlparse.parse_qsl(smart_str(q))) if q else {}
    query_dict.update((k, v) for k, v in query.items())

    query_string = urlencode([(k, v) for k, v in query_dict.items()
                               if v is not None])
    new = urlparse.ParseResult(url.scheme, url.netloc, url.path, url.params,
                               query_string, fragment)
    return new.geturl()


@register.inclusion_tag('input/pager.html')
@jinja2.contextfunction
def pager(context):
    """Fuckyeahpagination!"""
    page = context['page']
    url = context['request'].META['PATH_INFO']
    if page.has_previous():
        prev_url = urlparams(url, page=page.previous_page_number())

    if page.has_next():
        next_url = urlparams(url, page=page.next_page_number())

    return new_context(**locals())
