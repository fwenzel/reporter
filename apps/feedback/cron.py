import datetime
import logging
import sys

from django.db.models import Count
from django.conf import settings

import cronjobs
from textcluster import Corpus, search

from feedback.models import Opinion, Cluster, ClusterType, ClusterItem
from . import OS_USAGE

OPINION_THRESHOLD = 100
SIM_THRESHOLD = 8
NEW_WORDS = ['new', 'nice', 'love', 'like', 'great', ':)', '(:']
STOPWORDS = search.STOPWORDS
STOPWORDS.update(dict((w, 1,) for w in NEW_WORDS))

log = logging.getLogger('reporter')
log.debug = lambda x: sys.stdout.write(x+"\n")


@cronjobs.register
def fix_windows():
    ops = Opinion.objects.filter(os='win')

    # This should get the os to look right
    for op in ops:
        op.save()

@cronjobs.register
def cluster():
    # Get all the happy/sad issues in the last week.
    week_ago = datetime.datetime.today() - datetime.timedelta(7)
    three_days_ago = datetime.datetime.today() - datetime.timedelta(3)
    base_qs = Opinion.objects.filter(locale='en-US', created__gte=week_ago)

    log.debug('Beginning clustering')
    cluster_by_feeling(base_qs)
    log.debug('Removing old clusters')
    ClusterType.objects.filter(modified__lte=three_days_ago).delete()



def cluster_by_feeling(base_qs):
    happy = base_qs.filter(positive=True)
    sad = base_qs.filter(positive=False)
    log.debug('Clustering happy...')
    cluster_by_version(happy, 'happy')
    log.debug('Clustering sad...')
    cluster_by_version(sad, 'sad')

def cluster_by_version(qs, feeling):
    versions_qs = qs.values('version').annotate(Count('id'))
    versions = [v['version'] for v in versions_qs
                if v['id__count'] > OPINION_THRESHOLD]

    for version in versions:
        log.debug('Clustering %s, %s' % (feeling, version))
        cluster_by_platform(qs, feeling, version)

    # TODO(davedash): cluster all

def cluster_by_platform(qs, feeling, version):
    qs = qs.filter(version=version)
    # We need to create corpii for each platform and manually inspect each
    # opinion and put it in the right platform bucket.

    seen = {}

    for platform in OS_USAGE:
        c = Corpus(similarity=SIM_THRESHOLD, stopwords=STOPWORDS)
        seen = {}

        for op in qs.filter(os=platform.short):

            if op.description in seen:
                continue

            # filter short descriptions
            if len(op.description) < 15:
                continue

            seen[op.description] = 1
            c.add(op, str=op.description, key=op.id)

        result = c.cluster()

        if result:
            cluster_type, created = ClusterType.objects.get_or_create(
                    feeling=feeling,
                    version=version,
                    platform=platform.short,
                    frequency='weekly')
            cluster_type.created = datetime.datetime.now()
            cluster_type.save()

            # Remove the old cluster_groups
            Cluster.objects.filter(type=cluster_type).delete()

            # Store the clusters into groups
            for group in result:
                cluster = Cluster(type=cluster_type)
                cluster.num_opinions = len(group.similars) + 1
                cluster.pivot = group.primary
                cluster.save()

                for s in group.similars:
                    ClusterItem(cluster=cluster, opinion=s['object'],
                                score=s['similarity']).save()
