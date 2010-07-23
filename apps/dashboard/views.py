import datetime
from functools import wraps

from django.conf import settings
from django.db.models import Count

import jingo

from feedback import stats, FIREFOX, MOBILE
from feedback.models import Opinion, Term
from input.decorators import cache_page
from search.forms import ReporterSearchForm

from .forms import PeriodForm, PERIOD_DELTAS


@cache_page()
def dashboard(request):
    """Front page view."""
    search_form = ReporterSearchForm()
    period = PeriodForm()

    data = {'search_form': search_form, 'period': period,
            'messages_count': settings.MESSAGES_COUNT}
    template = 'dashboard/%sdashboard.html' % (
        'mobile/' if request.mobile_site else '')
    return jingo.render(request, template, data)


def period_to_date(f):
    """Decorator translating period string to dates."""
    @wraps(f)
    def wrapped(request, period='1d', *args, **kwargs):
        if period == 'all':
            start = None
        else:
            delta = PERIOD_DELTAS.get(period, datetime.timedelta(days=1))
            start = datetime.datetime.now() - delta
        return f(request, date_start=start, date_end=None)
    return wrapped


@cache_page()
@period_to_date
def sentiment(request, date_start, date_end):
    """AJAX action returning a summary of positive/negative sentiments."""
    opinions = Opinion.objects.between(date_start, date_end).filter(
        product=request.default_app.id)
    data = {'sent': stats.sentiment(qs=opinions)}
    return jingo.render(request, 'dashboard/sentiments.html', data)


@cache_page()
@period_to_date
def trends(request, date_start, date_end):
    """AJAX action returning a summary of frequent terms."""
    opinions = Opinion.objects.between(date_start, date_end).filter(
        product=request.default_app.id)
    frequent_terms = Term.objects.frequent(
        opinions=opinions)[:settings.TRENDS_COUNT]
    data = {'terms': stats.frequent_terms(qs=frequent_terms)}
    return jingo.render(request, 'dashboard/trends.html', data)


@cache_page()
@period_to_date
def demographics(request, date_start, date_end):
    """AJAX action returning an OS/locale summary."""
    opinions = Opinion.objects.between(date_start, date_end).filter(
        product=request.default_app.id)
    data = {'demo': stats.demographics(qs=opinions)}
    return jingo.render(request, 'dashboard/demographics.html', data)


@cache_page()
def messages(request, count=settings.MESSAGES_COUNT):
    """AJAX action returning the most recent messages."""
    opinions = Opinion.objects.filter(
        product=request.default_app.id).order_by('-created')[:count]
    data = {'opinions': opinions}
    return jingo.render(request, 'dashboard/messages.html', data)
