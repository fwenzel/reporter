import jingo

from client import Client
from forms import ReporterSearchForm
from feedback import stats


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

    return jingo.render(request, 'search/search.html', data)

