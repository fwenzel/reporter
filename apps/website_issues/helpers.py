import urllib

from django.core.urlresolvers import reverse
from django.utils.encoding import smart_unicode

from jingo import register

from .forms import DEFAULTS


@register.function
def sites_url(form, fragment_id=None, **kwargs):
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

    parts = [reverse("website_issues")]
    if len(parameters):
        parts.extend(["?", urllib.urlencode(parameters)])
    if fragment_id is not None:
        parts.extend(["#", fragment_id])
    return ''.join(parts)


@register.filter
def without_protocol(url):
    if url.find("://") == -1: return url
    return url[ url.find("://")+3 : ]


@register.filter
def protocol(url):
    return url[ : url.find("://")+3 ]


@register.filter
def as_unicode(str_or_unicode):
    return smart_unicode(str_or_unicode)
