import datetime

from django.conf import settings
from django.db.models import Count
from django.views.decorators.cache import cache_page

import jingo

from feedback import stats, FIREFOX, LATEST_BETAS
from feedback.models import Opinion, Term
from feedback.version_compare import simplify_version
from search.forms import ReporterSearchForm

from .forms import PeriodForm, PERIOD_DELTAS


# Dashboard defaults (TODO something other than Firefox)
DASH_PROD = FIREFOX
DASH_VER = simplify_version(LATEST_BETAS[FIREFOX])


def dashboard(request):
    search_form = ReporterSearchForm()
    period = PeriodForm()

    data = {'search_form': search_form, 'period': period}
    return jingo.render(request, 'dashboard/dashboard.html', data)


def period_to_date(f):
    """Decorator translating period string to dates."""
    def wrapped(request, period='1d', *args, **kwargs):
        if period == 'all':
            start = None
        else:
            delta = PERIOD_DELTAS.get(period, datetime.timedelta(days=1))
            start = datetime.datetime.now() - delta
        return f(request, date_start=start, date_end=None)
    return wrapped


@cache_page(settings.CACHE_DEFAULT_PERIOD)
@period_to_date
def sentiment(request, date_start, date_end):
    """AJAX action returning a summary of positive/negative sentiments."""
    opinions = Opinion.objects.between(date_start, date_end).filter(
        product=DASH_PROD.id, version=DASH_VER)
    data = {'sent': stats.sentiment(qs=opinions)}
    return jingo.render(request, 'dashboard/sentiments.html', data)


@cache_page(settings.CACHE_DEFAULT_PERIOD)
@period_to_date
def trends(request, date_start, date_end):
    """AJAX action returning a summary of frequent terms."""
    frequent_terms = Term.objects.frequent(
        date_start=date_start, date_end=date_end).filter(
            used_in__product=DASH_PROD.id, used_in__version=DASH_VER)[:10]
    # TODO use real product here
    data = {'terms': stats.frequent_terms(qs=frequent_terms)}
    return jingo.render(request, 'dashboard/trends.html', data)


@cache_page(settings.CACHE_DEFAULT_PERIOD)
@period_to_date
def demographics(request, date_start, date_end):
    """AJAX action returning an OS/locale summary."""
    opinions = Opinion.objects.between(date_start, date_end).filter(
        product=DASH_PROD.id, version=DASH_VER)
    # TODO use real product here
    data = {'demo': stats.demographics(qs=opinions)}
    return jingo.render(request, 'dashboard/demographics.html', data)


@cache_page(60 * 5)
def messages(request, count=10):
    """AJAX action returning the most recent messages."""
    opinions = Opinion.objects.filter(
        product=DASH_PROD.id, version=DASH_VER).order_by('-created')[:count]
    data = {'opinions': opinions}
    return jingo.render(request, 'dashboard/messages.html', data)
