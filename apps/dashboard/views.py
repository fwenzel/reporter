import json

from django.conf import settings

import jingo
from tower import ugettext as _

from feedback import stats, LATEST_BETAS
from feedback.models import Opinion, Term
from feedback.version_compare import simplify_version
from input.decorators import cache_page
from search.client import Client, SearchError
from search.forms import ReporterSearchForm, PROD_CHOICES, VERSION_CHOICES
from search.views import get_sentiment
from website_issues.models import SiteSummary


@cache_page
def dashboard(request):
    """Front page view."""

    # Defaults
    app = request.default_app
    version = simplify_version(LATEST_BETAS[app])

    # Frequent terms
    term_params = {
        'product': app.id,
        'version': version,
    }

    frequent_terms = Term.objects.frequent(
        **term_params)[:settings.TRENDS_COUNT]

    # opinions queryset for demographics
    latest_opinions = Opinion.objects.browse(**term_params)
    latest_beta = Opinion.objects.filter(version=version, product=app.id)

    # Sites clusters
    sites = SiteSummary.objects.filter(version__exact=version).filter(
        positive__exact=None).filter(os__exact=None)[:settings.TRENDS_COUNT]

    # search form to generate various form elements.
    search_form = ReporterSearchForm()

    try:
        c = Client()
        meta = ('positive', 'locale', 'os', 'day_sentiment', )

        search_opts = dict(product=app.short, version=version)
        c.query('', meta=meta, **search_opts)
        metas = c.meta
        daily = c.meta.get('day_sentiment', {})
        chart_data = dict(series=[
            dict(name=_('Praise'), data=daily['positive']),
            dict(name=_('Issues'), data=daily['negative']),
            ],
            )

        total = c.total_found
    except SearchError:
        metas = {}
        total = latest_beta.count()
        chart_data = None

    data = {'opinions': latest_opinions.all()[:settings.MESSAGES_COUNT],
            'opinion_count': total,
            'product': app.short,
            'products': PROD_CHOICES,
            'sentiments': get_sentiment(metas.get('positive', [])),
            'terms': stats.frequent_terms(qs=frequent_terms),
            'demo': dict(locale=metas.get('locale'), os=metas.get('os')),
            'sites': sites,
            'version': version,
            'versions': VERSION_CHOICES[app],
            'search_form': search_form,
            'chart_data_json': json.dumps(chart_data),
           }

    if not request.mobile_site:
        template = 'dashboard/dashboard.html'
    else:
        template = 'dashboard/mobile/dashboard.html'
    return jingo.render(request, template, data)
