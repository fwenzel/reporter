import datetime

from django.db.models import Count

from annoying.decorators import ajax_request, render_to

from feedback.models import Opinion, Term
from feedback import stats
from search.forms import ReporterSearchForm

from .forms import PeriodForm, PERIOD_DELTAS


@render_to('dashboard/dashboard.html')
def dashboard(request):
    search_form = ReporterSearchForm()
    period = PeriodForm()

    return {'search_form': search_form, 'period': period}


def period_to_date(f):
    """Decorator translating period string to dates."""
    def wrapped(request, *args, **kwargs):
        period = request.GET.get('period', '1d')
        delta = PERIOD_DELTAS.get(period, datetime.timedelta(days=1))
        start = datetime.datetime.now() - delta
        return f(request, date_start=start, date_end=None)
    return wrapped


@ajax_request
@period_to_date
def sentiment(request, date_start, date_end):
    """AJAX action returning a summary of positive/negative sentiments."""
    opinions = Opinion.objects.between(date_start, date_end)
    return stats.sentiment(qs=opinions)


@ajax_request
@period_to_date
def trends(request, date_start, date_end):
    """AJAX action returning a summary of frequent terms."""
    frequent_terms = Term.objects.frequent(
        date_start=date_start, date_end=date_end)[:10]
    return {'terms': stats.frequent_terms(qs=frequent_terms)}


@ajax_request
@period_to_date
def demographics(request, date_start, date_end):
    """AJAX action returning an OS/locale summary."""
    opinions = Opinion.objects.between(date_start, date_end)
    return stats.demographics(qs=opinions)


@ajax_request
def messages(request, count=10):
    """AJAX action returning the most recent messages."""
    opinions = Opinion.objects.order_by('-created')[:count]
    return {
        'msg': [ {'opinion': opinion.description,
                  'url': opinion.url,
                  'class': opinion.positive and 'happy' or 'sad'} for
                opinion in opinions ]}
