import datetime
import logging

from django.conf import settings
from django.db import transaction

import cronjobs
from textcluster import Corpus, search

import input
from feedback.models import Opinion
from input import (PLATFORM_USAGE, PRODUCT_USAGE, LATEST_BETAS, LATEST_RELEASE,
                   OPINION_PRAISE, OPINION_ISSUE, OPINION_IDEA)
from themes.models import Theme, Item

SIM_THRESHOLD = settings.CLUSTER_SIM_THRESHOLD
NEW_WORDS = ['new', 'nice', 'love', 'like', 'great', ':)', '(:']
STOPWORDS = search.STOPWORDS
STOPWORDS.update(dict((w, 1,) for w in NEW_WORDS))

log = logging.getLogger('reporter')


@cronjobs.register
@transaction.commit_on_success
def cluster():
    log.debug('Removing old clusters')
    Theme.objects.all().delete()
    # Get all the happy/sad issues in the last week.
    week_ago = datetime.datetime.today() - datetime.timedelta(7)

    base_qs = Opinion.objects.filter(locale='en-US', created__gte=week_ago)
    import pdb; pdb.set_trace()
    log.debug('Beginning clustering')
    cluster_by_product(base_qs)


def cluster_by_product(qs):
    for prod in PRODUCT_USAGE:
        version = prod.default_version
        log.debug('Clustering %s %s' % (unicode(prod.pretty), version))
        qs_product = qs.filter(product=prod.id, version=version)
        cluster_by_feeling(qs_product, prod)


def cluster_by_feeling(qs, prod):
    """Cluster all products by feeling."""
    for opinion_type in input.OPINION_USAGE:
        type_qs = qs.filter(_type=opinion_type.id)

        cluster_by_platform(type_qs, prod, opinion_type.short)


def cluster_by_platform(qs, prod, feeling):
    """
    Cluster all products/feelings by platform ('all' as well as separate
    platforms).
    """
    dimensions = dict(product=prod.id, feeling=feeling)
    cluster_and_save(qs, dimensions)

    # Create corpora for each platform and inspect each
    # opinion and put it in the right platform bucket.
    for platform in PLATFORM_USAGE:
        dimensions['platform'] = platform.short
        cluster_and_save(qs.filter(platform=platform.short),
                                  dimensions)


def cluster_and_save(qs, dimensions):
    result = cluster_queryset(qs)
    save_result(result, dimensions)


def cluster_queryset(qs):
    seen = {}
    c = Corpus(similarity=SIM_THRESHOLD, stopwords=STOPWORDS)

    for op in qs:

        if op.description in seen:
            continue

        # filter short descriptions
        if len(op.description) < 15:
            continue

        seen[op.description] = 1
        c.add(op, str=op.description, key=op.id)

    return c.cluster()


def save_result(result, dimensions):
    if result:
        for group in result:
            if (group.similars) < 5:
                continue

            topic = Theme(**dimensions)
            topic.num_opinions = len(group.similars) + 1
            topic.pivot = group.primary
            topic.save()

            for s in group.similars:
                Item(theme=topic, opinion=s['object'],
                     score=s['similarity']).save()
