from urllib import urlencode

from django.core.urlresolvers import reverse

from jingo import register
import jinja2

from feedback import FIREFOX

@register.function
def search_url(q=None, product=FIREFOX.short, version=None, locale=None,
               os=None, date_start=None, date_end=None):
    input = locals()

    search = reverse('search')
    data = {}

    # set defaults
    for (name, val) in input.items():
        if val:
            data[name] = val.encode('utf-8')

    return jinja2.Markup(u'%s?%s' % (search, urlencode(data)))
