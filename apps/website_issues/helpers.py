import urlparse

from django.utils.encoding import smart_unicode
from django.utils.http import urlencode

import jinja2
from jingo import register

from input.urlresolvers import reverse
from .forms import DEFAULTS


@register.function
@jinja2.contextfunction
def sites_url(context, form, url=None, **kwargs):
    """Return the current form values as URL parameters.

    Values are taken from the given form and can be overriden using kwargs.
    This is used to modify parts of a query without losing search context.
    The 'page' is always reset if not explicitly given.
    Parameters are only included if the values differ from the default.
    """
    parameters = form.cleaned_data.copy()
    # page is reset on every change of search
    for name in form.cleaned_data.keys():
        if name == 'page' or parameters[name] == DEFAULTS[name]:
            del parameters[name]
    for name, value in kwargs.iteritems():
        parameters[name] = value

    if url or context.get('site'):
        # single site URL
        _baseurl = url or context['site'].url
        _parsed = urlparse.urlparse(_baseurl)
        parts = [reverse('single_site', args=[_parsed.scheme, _parsed.netloc])]
        if 'q' in parameters:
            del parameters['q']
    else:
        # regular sites search URL
        parts = [reverse("website_issues")]

    if len(parameters):
        parts.extend(["?", urlencode(parameters)])

    return ''.join(parts)


@register.filter
def without_protocol(url_):
    """Extract the domain from a URL."""
    parsed = urlparse.urlparse(url_)
    return parsed.netloc


@register.filter
def protocol(url_):
    """Extract the protocol from a URL."""
    parsed = urlparse.urlparse(url_)
    return parsed.scheme


@register.filter
def as_unicode(str_or_unicode):
    return smart_unicode(str_or_unicode)
