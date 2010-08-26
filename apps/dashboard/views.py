import datetime
from functools import wraps

from django.conf import settings
from django.db.models import Count

import jingo

from product_details import firefox_versions

from feedback import stats, FIREFOX, MOBILE, LATEST_BETAS
from feedback.models import Opinion, Term
from feedback.version_compare import simplify_version
from input.decorators import cache_page
from search.forms import ReporterSearchForm, VERSION_CHOICES
from website_issues.models import SiteSummary
from .forms import PeriodForm, PERIOD_DELTAS


@cache_page
def dashboard(request):
    """Front page view."""
    if request.mobile_site:
        return dashboard_mobile(request)

    # Default app and version
    app_id = request.default_app.id
    version = firefox_versions['LATEST_FIREFOX_RELEASED_DEVEL_VERSION']

    # Frequent terms
    term_params = {
        'date_start': datetime.datetime.now() - datetime.timedelta(days=1),
        'product': app_id,
        'version': version,
    }
    frequent_terms = Term.objects.frequent(
        **term_params)[:settings.TRENDS_COUNT]

    # opinions queryset for demographics
    latest_opinions = Opinion.objects.browse(**term_params)

    # Sites clusters
    sites = SiteSummary.objects.filter(version__exact='<day>').filter(
        positive__exact=None)[:settings.TRENDS_COUNT]

    # search form to generate various form elements.
    search_form = ReporterSearchForm()

    data = {'opinions': latest_opinions.order_by('-created')[:settings.MESSAGES_COUNT],
            'opinion_count': latest_opinions.count(),
            'sentiments': stats.sentiment(qs=latest_opinions),
            'terms': stats.frequent_terms(qs=frequent_terms),
            'demo': stats.demographics(qs=latest_opinions),
            'sites': sites,
            'version': version,
            'versions': VERSION_CHOICES[request.default_app],
            'search_form': search_form}
    return jingo.render(request, 'dashboard/dashboard.html', data)


def dashboard_mobile(request):
    """Front page view for mobile."""
    # TODO Reintegrate this with the main dashboard view.
    search_form = ReporterSearchForm()
    period = PeriodForm()

    data = {'search_form': search_form, 'period': period,
            'messages_count': settings.MESSAGES_COUNT}
    template = 'dashboard/mobile/dashboard.html'
    return jingo.render(request, template, data)


def period_to_date(f):
    """
    Decorator translating period string to dates.

    Deprecated.
    """
    @wraps(f)
    def wrapped(request, period='1d', *args, **kwargs):
        if period == 'all':
            start = None
        else:
            delta = PERIOD_DELTAS.get(period, datetime.timedelta(days=1))
            start = datetime.datetime.now() - delta
        return f(request, date_start=start, date_end=None)
    return wrapped


@cache_page
@period_to_date
def sentiment(request, date_start, date_end):
    """
    AJAX action returning a summary of positive/negative sentiments.

    Deprecated.
    """
    opinions = Opinion.objects.between(date_start, date_end).filter(
        product=request.default_app.id,
        version=simplify_version(LATEST_BETAS[request.default_app]))
    data = {'sent': stats.sentiment(qs=opinions)}
    return jingo.render(request, 'dashboard/sentiments.html', data)


@cache_page
@period_to_date
def trends(request, date_start, date_end):
    """
    AJAX action returning a summary of frequent terms.

    Deprecated.
    """
    term_params = {
        'date_start': date_start,
        'date_end': date_end,
        'product': request.default_app.id,
        'version': simplify_version(LATEST_BETAS[request.default_app]),
    }
    frequent_terms = Term.objects.frequent(
        **term_params)[:settings.TRENDS_COUNT]
    data = {'terms': stats.frequent_terms(qs=frequent_terms)}
    return jingo.render(request, 'dashboard/trends.html', data)


@cache_page
@period_to_date
def demographics(request, date_start, date_end):
    """
    AJAX action returning an OS/locale summary.

    Deprecated.
    """
    opinions = Opinion.objects.between(date_start, date_end).filter(
        product=request.default_app.id,
        version=simplify_version(LATEST_BETAS[request.default_app]))
    data = {'demo': stats.demographics(qs=opinions)}
    return jingo.render(request, 'dashboard/demographics.html', data)


@cache_page
def messages(request, count=settings.MESSAGES_COUNT):
    """
    AJAX action returning the most recent messages.

    Deprecated.
    """
    opinions = Opinion.objects.filter(
        product=request.default_app.id,
        version=simplify_version(LATEST_BETAS[request.default_app])).order_by(
            '-created')[:count]
    data = {'opinions': opinions}
    return jingo.render(request, 'dashboard/messages.html', data)
