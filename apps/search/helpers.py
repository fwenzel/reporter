from urllib import urlencode


from jingo import register
import jinja2

from feedback.version_compare import simplify_version
from input.urlresolvers import reverse
from .forms import ReporterSearchForm


@register.function
@jinja2.contextfunction
def search_url(context, defaults=None, extra=None, feed=False, **kwargs):
    """Build a search URL with default values unless specified otherwise."""

    if feed:
        search = reverse('search.feed')
    else:
        search = reverse('search')
    if not defaults:
        defaults = {}
    data = []

    # fallbacks other than None
    fallbacks = {}
    if not 'products' in defaults and not 'products' in kwargs:
        fallbacks['product'] = context['request'].default_app.short

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

    return jinja2.Markup(u'%s?%s' % (search, urlencode(data)))
