import datetime
import json

from django.conf import settings
from django.contrib.syndication.views import Feed
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.utils.feedgenerator import Atom1Feed

import jingo
from tower import ugettext as _, ugettext_lazy as _lazy

from feedback import APPS, APP_IDS, FIREFOX, MOBILE, LATEST_BETAS
from feedback.version_compare import simplify_version
from input.decorators import cache_page
from input.urlresolvers import reverse

from .client import Client, SearchError
from .forms import ReporterSearchForm, PROD_CHOICES, VERSION_CHOICES


def _get_results(request, meta=[]):
    form = ReporterSearchForm(request.GET)
    if form.is_valid():
        query = form.cleaned_data.get('q', '')
        search_opts = form.cleaned_data
        product = form.cleaned_data['product'] or FIREFOX.short
        version = form.cleaned_data['version']
        search_opts['product'] = APPS[product].id
        search_opts['meta'] = meta
        c = Client()
        opinions = c.query(query, **search_opts)
        metas = c.meta
    else:
        query = ''
        opinions = []
        product = request.default_app
        version = simplify_version(LATEST_BETAS[product])
        metas = {}

    return (opinions, form, product, version, metas)


def get_sentiment(data=[]):
    r = dict(happy=0, sad=0, sentiment='happy')

    for el in data:
        if el['positive']:
            r['happy'] = el['count']
        else:
            r['sad'] = el['count']

    r['total'] = r['sad'] + r['happy']

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
        return reverse('search') + '?' + obj['request'].META['QUERY_STRING']

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
        categories = {'product': APP_IDS.get(item.product).short,
                      'version': item.version,
                      'os': item.os,
                      'locale': item.locale,
                      'sentiment': 'positive' if item.positive else 'negative',
                     }
        return (':'.join(i) for i in categories.items())

    def item_description(self, item):
        """A comment's main text."""
        return item.description

    def item_link(self, item):
        """Permalink per item. Also used as GUID."""
        # TODO make this a working link. bug 575770.
        return item.get_url_path()

    def item_pubdate(self, item):
        """Publishing date of a comment."""
        return item.created

    def item_title(self, item):
        """A comment's title."""
        return unicode(item)


@cache_page(use_get=True)
def index(request):
    try:
        meta = ('positive', 'locale', 'os', 'day_sentiment',)
        (results, form, product, version, metas) = _get_results(
                request, meta=meta)
    except SearchError, e:
        return jingo.render(request, 'search/unavailable.html',
                            {'search_error': e}, status=500)

    page = form.data.get('page', 1)

    if product == 'mobile':
        product = MOBILE
    else:
        product = FIREFOX

    data = {
        'form': form,
        'product': product.short,
        'products': PROD_CHOICES,
        'version': version,
        'versions': VERSION_CHOICES[product],
    }

    days = 0

    # Determine date period chosen
    if not getattr(form, 'cleaned_data', None):
        period = None
    else:
        end = form.cleaned_data.get('date_end')
        start = form.cleaned_data.get('date_start')
        _ago = lambda x: datetime.date.today() - datetime.timedelta(days=x)
        days = (end - start).days
        if (end == datetime.date.today() and start):
            period = {_ago(1): '1d',
                      _ago(7): '7d',
                      _ago(30): '30d'}.get(
                          form.cleaned_data.get('date_start'), 'custom')
        elif not form.cleaned_data.get('date_start'):
            period = 'infin'
        else:
            period = 'custom'
    data['period'] = period

    if results:
        pp = settings.SEARCH_PERPAGE
        pager = Paginator(results, pp)
        data['opinion_count'] = pager.count
        # If page request (e.g., 9999) is out of range, deliver last page of
        # results.
        try:
            data['page'] = pager.page(page)
        except (EmptyPage, InvalidPage):
            data['page'] = pager.page(pager.num_pages)

        data['opinions'] = data['page'].object_list
        data['sent'] = get_sentiment(metas.get('positive', []))
        data['demo'] = dict(locale=metas.get('locale'), os=metas.get('os'))
        if days > 10 or period == 'infin':
            daily = metas.get('day_sentiment', {})
            chart_data = dict(series=[
                dict(name=_('Praise'), data=daily['positive']),
                dict(name=_('Issues'), data=daily['negative']),
                ],
                )
            data['chart_data_json'] = json.dumps(chart_data)

    else:
        data.update({
            'opinion_count': 0,
            'opinions': None,
            'sent': get_sentiment(),
            'demo': {},
        })

    data['defaults'] = form.data

    template = 'search/%ssearch.html' % (
        'mobile/' if request.mobile_site else '')
    return jingo.render(request, template, data)
