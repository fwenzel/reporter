import itertools
import json
import time

from django.conf import settings

import jingo
from product_details import product_details
from product_details.version_compare import Version
from tower import ugettext as _

from feedback import stats
from feedback.models import Opinion, Term
from input import LATEST_BETAS, FIREFOX
from input.decorators import cache_page, forward_mobile, negotiate
from search.client import Client, SearchError
from search.forms import PROD_CHOICES, VERSION_CHOICES, ReporterSearchForm
from search.views import get_sentiment, release, get_defaults
from website_issues.models import SiteSummary


unixtime = lambda s: int(time.mktime(time.strptime(s, '%Y-%m-%d')))

def get_plotbands():
    plotbands = []
    color = itertools.cycle(('#fff', '#ddf'))
    to = int(time.time())
    versions = product_details.firefox_history_development_releases
    for version in FIREFOX.beta_versions:
        frm = unixtime(versions[version])
        plotband = dict(color=color.next(),
                        to=to,
                        label=dict(text=version))
        plotband['from'] = frm
        plotbands.append(plotband)
        to = frm
    return plotbands

@forward_mobile
@cache_page
def beta(request):
    """Beta dashboard."""
    # Defaults
    prod = request.default_prod
    version = Version(LATEST_BETAS[prod]).simplified

    search_form = ReporterSearchForm()
    # Frequent terms
    term_params = {
        'product': prod.id,
        'version': version,
    }

    frequent_terms = Term.objects.frequent(
        **term_params)[:settings.TRENDS_COUNT]

    # opinions queryset for demographics
    latest_opinions = Opinion.objects.browse(**term_params)
    latest_beta = Opinion.objects.filter(version=version, product=prod.id)

    # Sites clusters
    sites = SiteSummary.objects.filter(version__exact=version).filter(
        positive__exact=None).filter(platform__exact=None)[:settings.TRENDS_COUNT]

    try:
        c = Client()
        search_opts = dict(product=prod.short, version=version)
        c.query('', meta=('type', 'locale', 'platform', 'day_sentiment'),
                **search_opts)
        metas = c.meta
        daily = c.meta.get('day_sentiment', {})
        chart_data = dict(series=[
            dict(name=_('Praise'), data=daily['praise']),
            dict(name=_('Issues'), data=daily['issue']),
            dict(name=_('Ideas'), data=daily['idea']),
            ],
            plotBands=get_plotbands()
            )
        total = c.total_found
    except SearchError:
        metas = {}
        total = latest_beta.count()
        chart_data = None

    data = {'opinions': latest_opinions.all()[:settings.MESSAGES_COUNT],
            'opinion_count': total,
            'product': prod,
            'products': PROD_CHOICES,
            'sentiments': get_sentiment(metas.get('type', [])),
            'terms': stats.frequent_terms(qs=frequent_terms),
            'locales': metas.get('locale'),
            'platforms': metas.get('platform'),
            'sites': sites,
            'version': version,
            'versions': VERSION_CHOICES['beta'][prod],
            'chart_data_json': json.dumps(chart_data),
            'defaults': get_defaults(search_form),
            'search_form': search_form,
           }

    if not request.mobile_site:
        template = 'dashboard/beta.html'
    else:
        template = 'dashboard/mobile/beta.html'
    return jingo.render(request, template, data)


dashboard = negotiate(beta=beta, release=release)
