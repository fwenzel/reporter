import datetime
import json

from django.conf import settings
from django.contrib.syndication.views import Feed
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.utils.feedgenerator import Atom1Feed

import commonware.log
import jingo
from tower import ugettext as _, ugettext_lazy as _lazy

import input
from feedback.version_compare import simplify_version
from input import (APPS, APP_IDS, FIREFOX, MOBILE, LATEST_RELEASE,
                   LATEST_BETAS, LATEST_VERSION, OPINION_PRAISE, OPINION_ISSUE,
                   OPINION_SUGGESTION, OPINION_TYPES)
from input.decorators import cache_page
from input.urlresolvers import reverse
from search.client import Client, RatingsClient, SearchError
from search.forms import ReporterSearchForm, PROD_CHOICES, VERSION_CHOICES

log = commonware.log.getLogger('i.search')


def _get_results(request, meta=[], client=None):
    form = ReporterSearchForm(request.GET)
    if form.is_valid():
        data = form.cleaned_data
        query = data.get('q', '')
        product = data.get('product') or FIREFOX.short
        version = data.get('version')
        search_opts = _get_results_opts(request, data, product, meta)
        c = client or Client()
        opinions = c.query(query, **search_opts)
        metas = c.meta
    else:
        opinions = []
        product = request.default_app
        query = ''
        version = simplify_version(LATEST_VERSION()[product])
        metas = {}

    product = APPS.get(product, FIREFOX)

    return (opinions, form, product, version, metas)


def _get_results_opts(request, data, product, meta=[]):
    """Prepare the search options for the Sphinx query"""
    search_opts = data
    search_opts['product'] = APPS[product].id
    search_opts['meta'] = meta
    search_opts['offset'] = ((data.get('page', 1) - 1) *
                             settings.SEARCH_PERPAGE)

    sentiment = data.get('sentiment', '')
    if sentiment == 'happy':
        search_opts['type'] = OPINION_PRAISE.id
    elif sentiment == 'sad':
        search_opts['type'] = OPINION_ISSUE.id
    elif sentiment == 'suggestions':
        search_opts['type'] = OPINION_SUGGESTION.id

    return search_opts


def get_sentiment(data=[]):
    r = dict(happy=0, sad=0, suggestions=0, sentiment='happy')

    for el in data:
        if el['type'] == OPINION_PRAISE.id:
            r['happy'] = el['count']
        elif el['type'] == OPINION_ISSUE.id:
            r['sad'] = el['count']
        elif el['type'] == OPINION_SUGGESTION.id:
            r['suggestions'] = el['count']

    r['total'] = r['sad'] + r['happy'] + r['suggestions']

    if r['sad'] > r['happy']:
        r['sentiment'] = 'sad'

    return r


class SearchFeed(Feed):
    # TODO(davedash): Gracefully degrade for unavailable search.
    feed_type = Atom1Feed

    author_name = _lazy('Firefox Input')
    subtitle = _lazy("Search Results in Firefox Beta Feedback.")

    def get_object(self, request):
        data = dict(opinions=_get_results(request)[0], request=request)
        return data

    def link(self, obj):
        """Global feed link. Also used as GUID."""
        return u'%s?%s' % (reverse('search'),
                           obj['request'].META['QUERY_STRING'])

    def title(self, obj):
        """Global feed title."""
        request = obj['request']
        query = request.GET.get('q')

        # L10n: This is the title to the Search ATOM feed.
        return (_(u"Firefox Input: '{query}'").format(query=query) if query
                else _('Firefox Input'))

    def items(self, obj):
        """List of comments."""
        return obj['opinions'][:settings.SEARCH_PERPAGE]

    def item_categories(self, item):
        """Categorize comments. Style: "product:firefox" etc."""
        categories = {
            'product': APP_IDS.get(item.product).short,
            'version': item.version,
            'os': item.os,
            'locale': item.locale,
            'sentiment': OPINION_TYPES[item.type].short
        }

        return (':'.join(i) for i in categories.items())

    def item_description(self, item):
        """A comment's main text."""
        return item.description

    def item_link(self, item):
        """Permalink per item. Also used as GUID."""
        return item.get_url_path()

    def item_pubdate(self, item):
        """Publishing date of a comment."""
        return item.created

    def item_title(self, item):
        """A comment's title."""
        return unicode(item)


# TODO(davedash): use a bound form for defaults in views and get rid of this.
def get_defaults(form):
    """
    Keep form data as default options for further searches, but remove page
    from defaults so that every parameter change returns to page 1.
    """
    return dict((k, v) for k, v in form.data.items()
                if k != 'page' and k in form.fields)


def get_period(form):
    """Determine date period chosen."""
    days = 0

    if not getattr(form, 'cleaned_data', None):
        return None, days

    d = form.cleaned_data
    start = d.get('date_start')
    end = d.get('date_end') or datetime.date.today()

    if not (start and end):
        return 'infin', days

    _ago = lambda x: datetime.date.today() - datetime.timedelta(days=x)
    days = (end - start).days

    if (end == datetime.date.today() and start):
        return {_ago(1): '1d',
                _ago(7): '7d',
                _ago(30): '30d'}.get(start, 'custom'), days

    return 'custom', days


@cache_page(use_get=True)
def index(request):
    try:
        meta = ('type', 'locale', 'os', 'day_sentiment', 'manufacturer',
                'device')
        (results, form, product, version, metas) = _get_results(
                request, meta=meta)
    except SearchError, e:
        return jingo.render(request, 'search/unavailable.html',
                           {'search_error': e}, status=500)

    page = form.data.get('page', 1)

    data = dict(
        form=form,
        product=product,
        products=PROD_CHOICES,
        version=dict(form.fields['version'].choices).get(version or '--'),
        versions=VERSION_CHOICES['beta'][product],
    )

    data['period'], days = get_period(form)

    if results:
        pager = Paginator(results, settings.SEARCH_PERPAGE)
        data['opinion_count'] = pager.count
        # If page request (e.g., 9999) is out of range, deliver last page of
        # results.
        try:
            data['page'] = pager.page(page)
        except (EmptyPage, InvalidPage):
            data['page'] = pager.page(pager.num_pages)

        data['opinions'] = data['page'].object_list
        data['sent'] = get_sentiment(metas.get('type', {}))
        data['demo'] = dict(locale=metas.get('locale'), os=metas.get('os'),
                            manufacturer=metas.get('manufacturer'),
                            device=metas.get('device'))
        if days >= 7 or data['period'] == 'infin':
            daily = metas.get('day_sentiment', {})
            chart_data = dict(series=[
                dict(name=_('Praise'), data=daily['praise']),
                dict(name=_('Issues'), data=daily['issue']),
                dict(name=_('Suggestion'), data=daily['suggestion']),
                ],
            ) if daily else None
            data['chart_data_json'] = json.dumps(chart_data)
    else:
        data.update({
            'opinion_count': 0,
            'opinions': None,
            'sent': get_sentiment(),
            'demo': {},
        })

    data['defaults'] = get_defaults(form)
    template = 'search/%ssearch.html' % (
        'mobile/' if request.mobile_site else '')
    return jingo.render(request, template, data)


@cache_page(use_get=True)
def release(request):
    """Front page and search view for the release channel."""
    c = RatingsClient()
    metas = ['os', 'locale']

    for dimension in input.RATING_TYPES.keys():
        metas.append(dimension)
        metas.append('day__avg__%s' % dimension)

    try:
        (_, form, product, version, metas) = _get_results(request, metas,
                                                          client=c)
    except SearchError, e:
        return jingo.render(request, 'search/unavailable.html',
                           {'search_error': e}, status=500)

    rating_values = dict((k, unicode(v)) for k, v in input.RATING_CHOICES)

    series = []
    categories = []

    if 'ratings' in metas:
        for rating_value in rating_values:
            data = [v[rating_value] for k, v in metas['ratings'].items() if v]
            series.append(dict(name=rating_values[rating_value], data=data))

    ratings_chart = dict(series=series)
    categories = []
    charts = []

    if 'ratings_avg' in metas:
        for r in input.RATING_USAGE:
            categories.append(unicode(r.pretty))
            charts.append(dict(rating=r, json=json.dumps(dict(series=[dict(
                data=metas['ratings_avg'][r.id])]))))

    data = dict(
        product=product,
        products=PROD_CHOICES,
        version=dict(form.fields['version'].choices).get(version or '--'),
        versions=VERSION_CHOICES['release'][product],
        platforms=metas.get('os'),
        locales=metas.get('locale'),
        chart_json=json.dumps(ratings_chart),
        chart_categories=json.dumps(categories),
        avg_charts=charts,
        defaults=get_defaults(form),
        period=get_period(form)[0],
        search_form=form,
        total=c.total_found,
    )

    template = 'search/release.html'
    return jingo.render(request, template, data)
