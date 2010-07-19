from django.conf import settings
from django.contrib.syndication.views import Feed
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.utils.feedgenerator import Atom1Feed
from django.utils.hashcompat import md5_constructor

import jingo
from view_cache_utils import cache_page_with_prefix

from feedback import stats
from feedback.models import Term
from input.urlresolvers import reverse

from .client import Client, SearchError
from .forms import ReporterSearchForm


def _get_results(request):
    form = ReporterSearchForm(request.GET)

    if form.is_valid():
        query = form.cleaned_data.get('q', '')
        search_opts = form.cleaned_data

        c = Client()
        opinions = c.query(query, **search_opts)

    else:
        query = ''
        opinions = []

    return (opinions, form)


class SearchFeed(Feed):
    feed_type = Atom1Feed
    subtitle = "Feed of search results."

    def get_object(self, request):
        data = dict(opinions=_get_results(request)[0], request=request)
        return data

    def link(self, obj):
        return reverse('search') + '?' + obj['request'].META['QUERY_STRING']

    def title(self, obj):
        request = obj['request']
        query = request.GET.get('q')

        if query:
            return "Search for '%s'" % query

        return "Search for input"

    def items(self, obj):
        return obj['opinions']

    def item_link(self, item):
        return '/#%d' % item.id

    def item_description(self, item):
        return item.description


def search_view_cache_key(request):
    """Generate a cache key for a search view based on its GET parameters."""
    return md5_constructor(str(request.GET)).hexdigest()


@cache_page_with_prefix(settings.CACHE_DEFAULT_PERIOD, search_view_cache_key)
def index(request):
    try:
        (opinions, form) = _get_results(request)
    except SearchError, e:
        return jingo.render(request, 'search/unavailable.html',
                            {'search_error': e}, status=500)

    page = form.data.get('page', 1)

    data = {'form': form}
    pp = settings.SEARCH_PERPAGE

    if opinions:
        pager = Paginator(opinions, pp)
        # If page request (9999) is out of range, deliver last page of results.
        try:
            data['page'] = pager.page(page)
        except (EmptyPage, InvalidPage):
            data['page'] = pager.page(pager.num_pages)

        data['opinions'] = data['page'].object_list
        data['sent'] = stats.sentiment(qs=opinions)
        data['demo'] = stats.demographics(qs=opinions)

        frequent_terms = Term.objects.frequent(
            opinions=opinions)[:settings.TRENDS_COUNT]
        data['terms'] = stats.frequent_terms(qs=frequent_terms)

    return jingo.render(request, 'search/search.html', data)
