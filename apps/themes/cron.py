import datetime
import logging

from django.conf import settings
from django.db import transaction

import cronjobs
from textcluster import Corpus, search

from feedback.models import Opinion
from input import (CHANNEL_USAGE, PLATFORM_USAGE, PRODUCT_USAGE,
                   LATEST_BETAS, LATEST_RELEASE, OPINION_PRAISE,
                   OPINION_ISSUE, OPINION_IDEA)
from themes.models import Theme, Item

SIM_THRESHOLD = settings.CLUSTER_SIM_THRESHOLD
NEW_WORDS = ['new', 'nice', 'love', 'like', 'great', ':)', '(:']
STOPWORDS = search.STOPWORDS
STOPWORDS.update(dict((w, 1,) for w in NEW_WORDS))

log = logging.getLogger('reporter')


@cronjobs.register
def cluster_panorama():
    for word in ('panorama', 'tab candy',):
        print word
        print '=' * len(word)

        qs = Opinion.objects.filter(locale='en-US', version='4.0b5',
                positive=False, description__icontains=word)
        result = cluster_queryset(qs)

        for group in result:
            if len(group.similars) < 2:
                continue
            print '* ' + group.primary.description

            for s in group.similars:
                print '  * ' + s['object'].description


@cronjobs.register
@transaction.commit_on_success
def cluster():
    log.debug('Removing old clusters')
    Theme.objects.all().delete()
    # Get all the happy/sad issues in the last week.
    week_ago = datetime.datetime.today() - datetime.timedelta(7)

    base_qs = Opinion.objects.filter(locale='en-US', created__gte=week_ago)
    log.debug('Beginning clustering')
    cluster_by_product_and_channel(base_qs)


def cluster_by_product_and_channel(qs):
    def get_version(channel, prod):
        return LATEST_BETAS[prod] if channel == 'beta' else LATEST_RELEASE[prod]

    for channel in (c.short for c in CHANNEL_USAGE):
        for prod in PRODUCT_USAGE:
            version = get_version(channel, prod)
            log.debug('Clustering %s (%s: %s)' %
                      (unicode(prod.pretty), channel, version))
            qs_product = qs.filter(product=prod.id, version=version)
            cluster_beta_by_feeling(qs_product, channel, prod)


def cluster_beta_by_feeling(qs, channel, prod):
    """Cluster all products by feeling."""
    # Sentiments to be considered depend on channel.
    cluster_by = {
        'beta': (OPINION_PRAISE, OPINION_ISSUE, OPINION_IDEA),
        'release': (OPINION_IDEA,),
    }
    for op_type in cluster_by[channel]:
        type_qs = qs.filter(type=op_type.id)

        cluster_by_platform(type_qs, channel, prod, op_type.short)


def cluster_by_platform(qs, channel, prod, feeling):
    """
    Cluster all products/feelings by platform ('all' as well as separate
    platforms).
    """
    dimensions = dict(product=prod.id, channel=channel, feeling=feeling)
    cluster_and_save(qs, dimensions)

    # Beta only: Create corpora for each platform and inspect each
    # opinion and put it in the right platform bucket.
    if channel == 'beta':
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
