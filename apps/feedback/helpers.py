from django.core.urlresolvers import reverse
from django.template import defaultfilters
from django.utils import translation

from babel import Locale
from babel.support import Format
from jingo import register
import jinja2
import product_details

from feedback import OSES, OS_OTHER


# Yanking filters from Django.
register.filter(defaultfilters.iriencode)


@register.function
def url(viewname, *args, **kwargs):
    """Helper for Django's ``reverse`` in templates."""
    return reverse(viewname, args=args, kwargs=kwargs)


@register.function
def os_name(os):
    """Convert an OS short name into a human readable version."""
    return OSES.get(os, OS_OTHER).pretty


@register.function
def locale_name(locale, native=False, default='unknown'):
    """Convert a locale code into a human readable locale name."""
    if locale in product_details.languages:
        return product_details.languages[locale][
            native and 'native' or 'English']
    else:
        return default


def _get_format():
    lang = translation.get_language()
    locale = Locale(translation.to_locale(lang))
    return Format(locale)


@register.filter
def numberfmt(num, format=None):
    return _get_format().decimal(num, format)


@register.function
def smiley(style):
    """
    Renders a smiley.

    Style can be "sad" or "happy".
    """
    if not style in ('happy', 'sad'):
        return ''
    if style == 'happy': # positive smiley
        character = '&#9786;'
        title = 'happy face'
    else: # negative smiley
        character = '&#9785;'
        title = 'sad face'
    return jinja2.Markup(
        u'<span title="%s" class="smiley %s">%s</span>' % (
            title, style, character))
