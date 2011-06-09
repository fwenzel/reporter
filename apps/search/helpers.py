from urllib import urlencode


from jingo import register
import jinja2
from product_details.version_compare import Version

import input
from input.urlresolvers import reverse
from search.forms import ReporterSearchForm


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
    fallbacks = {'version': '--'}
    if not 'product' in defaults and not 'product' in kwargs:
        prod = context['request'].default_prod
        fallbacks['product'] = prod.short
        fallbacks['version'] = (getattr(prod, 'default_version', None) or
                                Version(input.LATEST_BETAS[prod]).simplified)

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
