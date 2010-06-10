import datetime

from django.conf import settings
from django.db.models import Count
from django.views.decorators.cache import cache_page

from annoying.decorators import ajax_request
import jingo

from feedback.models import Opinion, Term
from feedback import stats, FIREFOX
from search.forms import ReporterSearchForm

from .forms import PeriodForm, PERIOD_DELTAS


def dashboard(request):
    search_form = ReporterSearchForm()
    period = PeriodForm()

    data = {'search_form': search_form, 'period': period}
    return jingo.render(request, 'dashboard/dashboard.html', data)


def period_to_date(f):
    """Decorator translating period string to dates."""
    def wrapped(request, period='1d', *args, **kwargs):
        delta = PERIOD_DELTAS.get(period, datetime.timedelta(days=1))
        start = datetime.datetime.now() - delta
        return f(request, date_start=start, date_end=None)
    return wrapped


@cache_page(settings.CACHE_DEFAULT_PERIOD)
@ajax_request
@period_to_date
def sentiment(request, date_start, date_end):
    """AJAX action returning a summary of positive/negative sentiments."""
    opinions = Opinion.objects.between(date_start, date_end)
    return stats.sentiment(qs=opinions)


@cache_page(settings.CACHE_DEFAULT_PERIOD)
@period_to_date
def trends(request, date_start, date_end):
    """AJAX action returning a summary of frequent terms."""
    frequent_terms = Term.objects.frequent(
        date_start=date_start, date_end=date_end)[:10]
    # TODO use real product here
    data = {'terms': stats.frequent_terms(qs=frequent_terms),
            'prod': FIREFOX.short}
    return jingo.render(request, 'dashboard/trends.html', data)


@cache_page(settings.CACHE_DEFAULT_PERIOD)
@period_to_date
def demographics(request, date_start, date_end):
    """AJAX action returning an OS/locale summary."""
    opinions = Opinion.objects.between(date_start, date_end)
    # TODO use real product here
    data = {'demo': stats.demographics(qs=opinions),
            'prod': FIREFOX.short }
    return jingo.render(request, 'dashboard/demographics.html', data)


@cache_page(60 * 5)
@ajax_request
def messages(request, count=10):
    """AJAX action returning the most recent messages."""
    opinions = Opinion.objects.order_by('-created')[:count]
    return {
        'msg': [ {'opinion': opinion.description,
                  'url': opinion.url,
                  'class': opinion.positive and 'happy' or 'sad'} for
                opinion in opinions ]}
