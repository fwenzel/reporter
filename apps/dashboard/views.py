import datetime
from functools import wraps
import json
import random
import time

from django.conf import settings

import jingo
from tower import ugettext as _

from feedback import stats, LATEST_BETAS
from feedback.models import Opinion, Term
from feedback.version_compare import simplify_version
from input.decorators import cache_page
from search.client import Client
from search.forms import ReporterSearchForm, PROD_CHOICES, VERSION_CHOICES
from search.views import get_sentiment
from website_issues.models import SiteSummary


@cache_page
def dashboard(request):
    """Front page view."""

    # Defaults
    app = request.default_app
    version = simplify_version(LATEST_BETAS[app])
    num_days = 1
    dashboard_defaults = {
        'product': app.short,
        'version': version,
        'num_days': "%s%s" % (num_days, 'd'),
    }

    # Frequent terms
    term_params = {
        'date_start': (datetime.datetime.now() -
                       datetime.timedelta(days=num_days)),
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
        positive__exact=None).filter(os__exact=None)[:settings.TRENDS_COUNT]

    # Historical feedback data for chart.
    # TODO L10n
    # TODO use real data here, un-import random.
    rnd_data = lambda: [random.randint(0, 1000) for i in xrange(24)]
    chart_data = {
        'categories': ['%dh' % ((int(time.strftime('%H')) + i) % 24) for i in
                       xrange(24)],
        # TODO use real data here, un-import random.
        'series': [{'name': _('Positive'),
                    'data': rnd_data(),
                   },
                   {'name': _('Negative'),
                    'data': rnd_data(),
                   },
                   {'name': _('Ideas'),
                    'data': rnd_data(),
                   }],
    }

    # search form to generate various form elements.
    search_form = ReporterSearchForm()

    search_opts = {}
    search_opts['date_end'] = datetime.date.today()
    search_opts['date_start'] = (search_opts['date_end'] -
                                 datetime.timedelta(days=30))

    try:
        c = Client()
        c.query('', meta=('positive', 'locale', 'os',), **search_opts)
        metas = c.meta
        total = c.total_found
    except:
        metas = {}
        total = latest_beta.count()

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
            'dashboard_defaults': dashboard_defaults,
            'search_form': search_form,
            'chart_data_json': json.dumps(chart_data),
           }

    if not request.mobile_site:
        template = 'dashboard/dashboard.html'
    else:
        template = 'dashboard/mobile/dashboard.html'
    return jingo.render(request, template, data)
