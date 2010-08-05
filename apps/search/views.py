from django.conf import settings
from django.contrib.syndication.views import Feed
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.utils.feedgenerator import Atom1Feed

import jingo
from tower import ugettext as _, ugettext_lazy as _lazy

from feedback import APP_IDS, stats
from feedback.models import Term
from input.decorators import cache_page
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
        return (_("Firefox Input: '{query}'").format(query=query) if query else
                _('Firefox Input'))

    def items(self, obj):
        """List of comments."""
        return obj['opinions']

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
        return '/#%d' % item.id

    def item_pubdate(self, item):
        """Publishing date of a comment."""
        return item.created

    def item_title(self, item):
        """A comment's title."""
        return unicode(item)


@cache_page(use_get=True)
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

        #frequent_terms = Term.objects.frequent(
        #    opinions=(o.id for o in opinions))[:settings.TRENDS_COUNT]
        #data['terms'] = stats.frequent_terms(qs=frequent_terms)

    template = 'search/%ssearch.html' % (
        'mobile/' if request.mobile_site else '')
    return jingo.render(request, template, data)
