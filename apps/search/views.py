from django.conf import settings

import jingo

from feedback import stats
from feedback.models import Term

from .client import Client
from .forms import ReporterSearchForm


def index(request):
    form = ReporterSearchForm(request.GET)
    data = {'form': form}

    if form.is_valid():
        query = form.cleaned_data.get('q', '')
        search_opts = form.cleaned_data
        c = Client()
        opinions = c.query(query, **search_opts)
    else:
        query = ''
        opinions = None

    if opinions:
        data['opinions'] = opinions
        data['sent'] = stats.sentiment(qs=opinions)
        data['demo'] = stats.demographics(qs=opinions)

        frequent_terms = opinions.terms.frequent()Term.objects.frequent().filter(
            used_in__in=opinions)[:settings.TRENDS_COUNT]
        data['terms'] = stats.frequent_terms(qs=frequent_terms)

    return jingo.render(request, 'search/search.html', data)
