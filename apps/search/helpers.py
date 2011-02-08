from urllib import urlencode


from jingo import register
import jinja2

import input
from feedback import LATEST_VERSION
from feedback.version_compare import simplify_version
from input.urlresolvers import reverse
from .forms import ReporterSearchForm


@register.function
@jinja2.contextfunction
def search_url(context, defaults=None, extra=None, feed=False, **kwargs):
    """Build a search URL with default values unless specified otherwise."""
    channel = input.get_channel()
    if channel == 'release':
        search = reverse('dashboard')
    elif feed:
        search = reverse('search.feed')
    else:
        search = reverse('search')
    if not defaults:
        defaults = {}
    data = []

    # fallbacks other than None
    fallbacks = {'version': '--'}
    if not 'product' in defaults and not 'product' in kwargs:
        app = context['request'].default_app
        fallbacks['product'] = app.short
        fallbacks['version'] = simplify_version(LATEST_VERSION()[app])

    # get field data from keyword args or defaults
    for field in ReporterSearchForm.base_fields:
        val = kwargs.get(field, defaults.get(
            field, fallbacks.get(field, None)))
        if val:
            data.append((field, unicode(val).encode('utf-8')))

    # append extra fields
    if extra:
        data = dict(data)
        data.update(extra)

    return u'%s?%s' % (search, urlencode(data))
