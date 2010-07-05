from django.conf import settings
from django.utils.hashcompat import md5_constructor

import jingo
from view_cache_utils import cache_page_with_prefix

from feedback import stats
from feedback.models import Opinion, Term

from .client import Client, SearchError
from .forms import ReporterSearchForm


def search_view_cache_key(request):
    """Generate a cache key for a search view based on its GET parameters."""
    return md5_constructor(str(request.GET)).hexdigest()


@cache_page_with_prefix(settings.CACHE_DEFAULT_PERIOD, search_view_cache_key)
def index(request):
    form = ReporterSearchForm(request.GET)
    data = {'form': form}

    if form.is_valid():
        query = form.cleaned_data.get('q', '')
        if not query:
            # browse mode
            opinions = Opinion.objects.browse(**form.cleaned_data)
        else:
            # search mode
            search_opts = form.cleaned_data
            try:
                c = Client()
                opinions = c.query(query, **search_opts)
            except SearchError, e:
                return jingo.render(request, 'search/unavailable.html',
                                    {'search_error': e}, status=500)

    else:
        query = ''
        opinions = None

    if opinions:
        data['sent'] = stats.sentiment(qs=opinions)
        data['demo'] = stats.demographics(qs=opinions)

        frequent_terms = Term.objects.frequent().filter(
            used_in__in=opinions)[:settings.TRENDS_COUNT]
        data['terms'] = stats.frequent_terms(qs=frequent_terms)
        # TODO paginate instead of just limiting to 20!
        data['opinions'] = opinions[:20]

    return jingo.render(request, 'search/search.html', data)
