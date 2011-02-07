import json

from input import APP_USAGE, get_channel
from search.forms import VERSION_CHOICES, ReporterSearchForm


def product_versions(request):
    return {
        'PROD_VERSIONS_JSON': json.dumps(dict(
            [(p.short, [(v[0], unicode(v[1])) for v in
             VERSION_CHOICES[get_channel()][p]]) for
             p in APP_USAGE]))
    }
