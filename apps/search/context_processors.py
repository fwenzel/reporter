import json

from input import PRODUCT_USAGE
from search.forms import VERSION_CHOICES


def product_versions(request):
    return {
        'PROD_VERSIONS_JSON': json.dumps(dict(
            [(p.short, [(v[0], unicode(v[1])) for v in
             VERSION_CHOICES[p]]) for p in PRODUCT_USAGE]))
    }
