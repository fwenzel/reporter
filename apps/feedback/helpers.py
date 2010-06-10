from django.core.urlresolvers import reverse
from django.template import defaultfilters

from jingo import register
import jinja2

# Yanking filters from Django.
register.filter(defaultfilters.iriencode)

@register.function
def url(viewname, *args, **kwargs):
    """Helper for Django's ``reverse`` in templates."""
    return reverse(viewname, args=args, kwargs=kwargs)


@register.function
def smiley(style):
    """
    Renders a big smiley.
    style can be "sad" or "happy".
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
        u'<span title="%s" class="smiley">%s</span>' % (title, character))
