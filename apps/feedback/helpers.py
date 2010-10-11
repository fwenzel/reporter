from jingo import register
import jinja2
from product_details import product_details
from tower import ugettext as _, ugettext_lazy as _lazy

from feedback import OSES, OS_OTHER


@register.function
def os_name(os):
    """Convert an OS short name into a human readable version."""
    return OSES.get(os, OS_OTHER).pretty


@register.function
def locale_name(locale, native=False, default=_lazy('unknown')):
    """Convert a locale code into a human readable locale name."""
    if locale in product_details.languages:
        return product_details.languages[locale][
            native and 'native' or 'English']
    else:
        return default


@register.function
def smiley(style, page=None):
    """
    Renders a smiley.

    Style can be "sad" or "happy".
    """
    if not style in ('happy', 'sad'):
        return ''
    if style == 'happy': # positive smiley
        character = '&#9786;'
        title = _('Praise')
    else: # negative smiley
        character = '&#9785;'
        title = _('Issue')
    return jinja2.Markup(
        u'<span title="%s" class="smiley %s %s">%s</span>' % (
            title, style, page, character))
