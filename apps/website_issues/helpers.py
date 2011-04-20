import utils

from django.utils.encoding import smart_unicode

import jinja2
from jingo import register

from input.helpers import urlparams
from input.urlresolvers import reverse


@register.function
@jinja2.contextfunction
def sites_url(context, url, **kw):
    _parsed = utils.urlparse(url)
    base_url = reverse('single_site', args=[_parsed.scheme, _parsed.netloc])
    base_url = base_url + '?' + context['request'].META['QUERY_STRING']
    return urlparams(base_url, page=None)


@register.filter
def strip_protocol(url_):
    """Strip protocol from urls with exceptions for chrome:// and about:."""
    parsed = utils.urlparse(url_)
    if parsed.scheme in ('about', 'chrome'):
        return url_
    else:
        return parsed.netloc


@register.filter
def domain(url_):
    """Remove the protocol from a sites URL (path has been removed already)"""
    parsed = utils.urlparse(url_)
    if parsed.scheme == 'chrome':
        return url_[len('chrome://'):]
    else:
        return parsed.netloc


@register.filter
def protocol(url_):
    """Extract the protocol from a URL."""
    parsed = utils.urlparse(url_)
    return parsed.scheme


@register.filter
def as_unicode(str_or_unicode):
    return smart_unicode(str_or_unicode)
