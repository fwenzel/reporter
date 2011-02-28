from collections import namedtuple

from django.conf import settings
from django import http
from django.core.paginator import Paginator, InvalidPage, EmptyPage

import jingo
from tower import ugettext as _

from input import (CHANNEL_BETA, CHANNEL_RELEASE,
                   OPINION_PRAISE, OPINION_ISSUE, OPINION_IDEA,
                   PRODUCTS, PLATFORMS, FIREFOX, PRODUCT_USAGE,
                   get_channel)
from input.decorators import cache_page, negotiate
from input.helpers import urlparams
from input.urlresolvers import reverse
from themes.models import Theme


Filter = namedtuple('Filter', 'url text title selected')


def _get_sentiments(request, sentiment):
    """Get available sentiment filters (beta channel only)."""
    sentiments = []
    url = request.get_full_path()

    f = Filter(urlparams(url, s=None), _('All'),  _('All feedback'),
               not sentiment)
    sentiments.append(f)

    f = Filter(urlparams(url, s=OPINION_PRAISE.short), _('Praise'),
               _('Praise only'), (sentiment == OPINION_PRAISE.short))
    sentiments.append(f)

    f = Filter(urlparams(url, s=OPINION_ISSUE.short), _('Issues'),
               _('Issues only'), (sentiment == OPINION_ISSUE.short))
    sentiments.append(f)

    f = Filter(urlparams(url, s=OPINION_IDEA.short), _('Ideas'),
               _('Ideas only'), (sentiment == OPINION_IDEA.short))
    sentiments.append(f)

    return sentiments


def _get_platforms(request, product, platform):
    """Get platforms (beta channel only)."""
    platforms = []
    url = request.get_full_path()

    f = Filter(urlparams(url, p=None), _('All'), _('All Platforms'),
               (not platform))
    platforms.append(f)
    platforms_from_db = (Theme.objects.filter(product=PRODUCTS[product].id)
                         .values_list('platform', flat=True)
                         .distinct().order_by('platform'))

    for p in platforms_from_db:
        if not p:
            continue
        f = Filter(urlparams(url, p=p), p, PLATFORMS[p].pretty,
                   (platform == p))
        platforms.append(f)

    return platforms


def _get_products(request, product):
    """Get product filters (all channels)."""
    products = []
    url = request.get_full_path()

    for prod in PRODUCT_USAGE:
        f = Filter(urlparams(url, a=prod.short), prod.pretty, prod.pretty,
                   (product == prod.short))
        products.append(f)

    return products


@cache_page(use_get=True)
def beta_index(request):
    """List the themes clusters for beta releases."""

    qs = Theme.objects.filter(channel=CHANNEL_BETA.short)
    product = request.GET.get('a', FIREFOX.short)
    products = _get_products(request, product)
    try:
        qs = qs.filter(product=PRODUCTS[product].id)
    except KeyError:
        raise http.Http404

    sentiment = request.GET.get('s')
    sentiments = _get_sentiments(request, sentiment)
    if sentiment:
        qs = qs.filter(feeling=sentiment)

    platform = request.GET.get('p', '')
    platforms = _get_platforms(request, product, platform)
    # platform = '' indicates ALL
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
def release_index(request):
    """List the themes clusters for major releases."""

    qs = Theme.objects.filter(channel=CHANNEL_RELEASE.short,
                              feeling=OPINION_IDEA.short)
    product = request.GET.get('a', FIREFOX.short)
    products = _get_products(request, product)
    try:
        qs = qs.filter(product=PRODUCTS[product].id)
    except KeyError:
        raise http.Http404

    args = dict(products=products)
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

index = negotiate(beta=beta_index, release=release_index)


@cache_page(use_get=True)
def theme(request, theme_id):
    try:
        theme = Theme.objects.get(id=theme_id, channel=get_channel())
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
