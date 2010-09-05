import datetime
from functools import wraps

from django.conf import settings
from django.db.models import Count

import jingo

from product_details import firefox_versions

from feedback import stats, LATEST_BETAS
from feedback.models import Opinion, Term
from feedback.version_compare import simplify_version
from input.decorators import cache_page
from search.forms import ReporterSearchForm, VERSION_CHOICES
from website_issues.models import SiteSummary


@cache_page
def dashboard(request):
    """Front page view."""

    # Default app and version
    app = request.default_app
    version = simplify_version(LATEST_BETAS[app])

    # Frequent terms
    term_params = {
        'date_start': datetime.datetime.now() - datetime.timedelta(days=1),
        'product': app.id,
        'version': version,
    }
    frequent_terms = Term.objects.frequent(
        **term_params)[:settings.TRENDS_COUNT]

    # opinions queryset for demographics
    latest_opinions = Opinion.objects.browse(**term_params)
    latest_beta = Opinion.objects.filter(version=version, product=app.id)

    # Sites clusters
    sites = SiteSummary.objects.filter(version__exact='<day>').filter(
        positive__exact=None)[:settings.TRENDS_COUNT]

    # search form to generate various form elements.
    search_form = ReporterSearchForm()

    data = {'opinions': latest_opinions.order_by('-created')[:settings.MESSAGES_COUNT],
            'opinion_count': latest_beta.count(),
            'sentiments': stats.sentiment(qs=latest_opinions),
            'terms': stats.frequent_terms(qs=frequent_terms),
            'demo': stats.demographics(qs=latest_opinions),
            'sites': sites,
            'version': version,
            'versions': VERSION_CHOICES[app],
            'search_form': search_form}

    if not request.mobile_site:
        template= 'dashboard/dashboard.html'
    else:
        template = 'dashboard/mobile/dashboard.html'
    return jingo.render(request, template, data)
