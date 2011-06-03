import datetime
import urlparse

from django.conf import settings
from django.template import defaultfilters
from django.utils import translation
from django.utils.encoding import smart_str
from django.utils.http import urlencode
from django.utils.safestring import mark_safe

from babel import Locale, UnknownLocaleError
from babel.support import Format
from jingo import register
import jinja2
import pytz
from tower import ugettext as _, ungettext as ngettext

from .urlresolvers import reverse
from themes.helpers import new_context

# Yanking filters from Django.
register.filter(defaultfilters.iriencode)
register.filter(defaultfilters.slugify)
register.filter(defaultfilters.truncatewords)


def _get_format():
    lang = translation.get_language()
    try:
        locale = Locale(translation.to_locale(lang))
    except UnknownLocaleError:
        locale = Locale(translation.to_locale(settings.BABEL_FALLBACK.get(
            lang, 'en-US')))
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

@register.filter
def time(time):
    """
    Return a <time> tag with a locale-formatted time inside the title
    attribute and an HTML5 datetime attribute formatted time inside the
    datetime attribute.
    
    The content of the time tag itself will be the result of timesince(time).
    """
    return mark_safe(
        u'<time datetime="{isotime}" title="{time}">{ago}</time>'.format(
            ago=timesince(time),
            isotime=isotime(time),
            time=babel_datetime(time)))


@register.filter
def timesince(t):
    """Show relative time deltas. > 7 days, fall back to babel_date."""
    diff = (datetime.datetime.now() - t)
    if diff.days > 7:
        return babel_date(t)
    elif diff.days > 0:
        return ngettext('{0} day ago', '{0} days ago',
                        diff.days).format(diff.days)
    else:
        minutes = diff.seconds / 60
        hours = minutes / 60
        if hours > 0:
            return ngettext('{0} hour ago', '{0} hours ago',
                            hours).format(hours)
        elif minutes > 0:
            return ngettext('{0} minute ago', '{0} minutes ago',
                            minutes).format(minutes)
        else:
            # L10n: This means an event that happened only a few seconds ago.
            return _('just now')


@register.function
@jinja2.contextfunction
def absolute_url(context, relative):
    """Given a relative URL, build an absolute URL including domain."""
    return context['request'].build_absolute_uri(relative)


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
    page = context.get('page')
    if page:
        url = context['request'].META['PATH_INFO']
        if page.has_previous():
            prev_url = urlparams(url, page=page.previous_page_number())

        if page.has_next():
            next_url = urlparams(url, page=page.next_page_number())

    return new_context(**locals())


@register.filter
def truncchar(value, arg):
    """Rruncate after a certain number of characters."""
    if len(value) < arg:
        return value
    else:
        return value[:arg] + '...'
