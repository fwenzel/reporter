from collections import namedtuple

import jingo
from tower import ugettext as _

from feedback import OSES
from input.decorators import cache_page
from input.helpers import urlparams
from themes.models import Theme


Filter = namedtuple('Filter', 'url text title selected')


def _get_sentiments(request, sentiment):
    sentiments = []
    url = request.get_full_path()

    f = Filter(urlparams(url, s=None), _('All'),  _('All feedback'),
               not sentiment)

    sentiments.append(f)

    f = Filter(urlparams(url, s='happy'), _('Praise'),  _('Praise only'),
               (sentiment == 'happy'))

    sentiments.append(f)

    f = Filter(urlparams(url, s='sad'), _('Issues'),  _('Issues only'),
               (sentiment == 'sad'))

    sentiments.append(f)
    return sentiments


def _get_platforms(request, platform):
    platforms = []
    url = request.get_full_path()

    f = Filter(urlparams(url, p=None), _('All'), _('All Platforms'),
               (not platform))
    platforms.append(f)

    platforms_from_db = (Theme.objects.values_list('platform', flat=True)
                         .distinct().order_by('platform'))

    for p in platforms_from_db:
        f = Filter(urlparams(url, p=p), p, OSES[p].pretty,
                   (platform == p))
        platforms.append(f)

    return platforms


@cache_page(use_get=True)
def index(request):
    """List the various clusters of data we have."""

    qs = Theme.objects.all()

    sentiment = request.GET.get('s')
    sentiments = _get_sentiments(request, sentiment)
    if sentiment:
        qs = qs.filter(feeling=sentiment)

    platform = request.GET.get('p')
    platforms = _get_platforms(request, platform)
    if platform:
        qs = qs.filter(platform=platform)

    args = dict(themes=qs, sentiments=sentiments, platforms=platforms)
    return jingo.render(request, 'themes/index.html', args)
