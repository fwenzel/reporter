from collections import namedtuple

from django.conf import settings
from django import http
from django.core.paginator import Paginator, InvalidPage, EmptyPage

import jingo
from tower import ugettext as _

from feedback import APPS, OSES, FIREFOX, APP_USAGE, OPINION_PRAISE, OPINION_ISSUE, OPINION_SUGGESTION
from input.decorators import cache_page
from input.helpers import urlparams
from input.urlresolvers import reverse
from themes.models import Theme


Filter = namedtuple('Filter', 'url text title selected')


def _get_sentiments(request, sentiment):
    sentiments = []
    url = request.get_full_path()

    f = Filter(urlparams(url, s=None), _('All'),  _('All feedback'),
               not sentiment)

    sentiments.append(f)

    f = Filter(urlparams(url, s='happy'), _('Praise'),  _('Praise only'),
               (sentiment == 'happy'))

    sentiments.append(f)

    f = Filter(urlparams(url, s='sad'), _('Issues'),  _('Issues only'),
               (sentiment == 'sad'))

    sentiments.append(f)

    f = Filter(urlparams(url, s='suggestions'), _('Suggestions'),
            _('Suggestions only'),
               (sentiment == 'suggestions'))

    sentiments.append(f)
    return sentiments


def _get_platforms(request, platform):
    platforms = []
    url = request.get_full_path()

    f = Filter(urlparams(url, p=None), _('All'), _('All Platforms'),
               (not platform))
    platforms.append(f)

    platforms_from_db = (Theme.objects.values_list('platform', flat=True)
                         .distinct().order_by('platform'))

    for p in platforms_from_db:
        f = Filter(urlparams(url, p=p), p, OSES[p].pretty,
                   (platform == p))
        platforms.append(f)

    return platforms


def _get_products(request, product):
    products = []
    url = request.get_full_path()

    for app in APP_USAGE:
        f = Filter(urlparams(url, a=app.short), app.pretty, app.pretty,
                   (product == app.short))
        products.append(f)

    return products


@cache_page(use_get=True)
def index(request):
    """List the various clusters of data we have."""

    qs = Theme.objects.all()
    product = request.GET.get('a', FIREFOX.short)
    products = _get_products(request, product)
    try:
        qs = qs.filter(product=APPS[product].id)
    except KeyError:
        raise http.Http404

    sentiment = request.GET.get('s')
    sentiments = _get_sentiments(request, sentiment)
    if sentiment:
        qs = qs.filter(feeling=sentiment)

    platform = request.GET.get('p')
    platforms = _get_platforms(request, platform)
    if platform:
        qs = qs.filter(platform=platform)

    args = dict(sentiments=sentiments, platforms=platforms, products=products)
    page = request.GET.get('page', 1)

    if qs:
        pp = settings.SEARCH_PERPAGE
        pager = Paginator(qs.select_related(), pp)

        try:
            args['page'] = pager.page(page)
        except (EmptyPage, InvalidPage):
            args['page'] = pager.page(pager.num_pages)

        args['themes'] = args['page'].object_list

    return jingo.render(request, 'themes/index.html', args)


@cache_page(use_get=True)
def theme(request, theme_id):
    try:
        theme = Theme.objects.get(id=theme_id)
    except Theme.DoesNotExist:
        raise http.Http404

    pager = Paginator(theme.opinions.all(), settings.SEARCH_PERPAGE)
    try:
        page = pager.page(request.GET.get('page', 1))
    except (EmptyPage, InvalidPage):
        page = pager.page(pager.num_pages)

    return jingo.render(request,
                        'themes/theme.html',
                        {"theme": theme,
                         "opinions": page.object_list,
                         "page": page,
                         "exit_url": reverse("themes")})
