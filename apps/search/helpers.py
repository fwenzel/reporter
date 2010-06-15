from urllib import urlencode

from django.core.urlresolvers import reverse

from jingo import register
import jinja2

from feedback import FIREFOX
from .forms import ReporterSearchForm

@register.function
def search_url(defaults=None, extra=None, **kwargs):
    """Build a search URL with default values unless specified otherwise."""
    search = reverse('search')
    if not defaults:
        defaults = {}
    data = []

    # fallbacks other than None
    fallbacks = {
        'product': FIREFOX.short,
    }

    # get field data from keyword args or defaults
    for field in ReporterSearchForm.base_fields:
        val = kwargs.get(field, defaults.get(
            field, fallbacks.get(field, None)))
        if val:
            data.append((field, unicode(val).encode('utf-8')))

    # append extra fields
    if extra:
        data += extra.items()

    return jinja2.Markup(u'%s?%s' % (search, urlencode(data)))
