import datetime
import logging
import sys

from django.conf import settings

import cronjobs
from textcluster import Corpus, search

from feedback import OS_USAGE, FIREFOX, LATEST_BETAS
from feedback.models import Opinion
from themes.models import Theme, Item

SIM_THRESHOLD = settings.CLUSTER_SIM_THRESHOLD
NEW_WORDS = ['new', 'nice', 'love', 'like', 'great', ':)', '(:']
STOPWORDS = search.STOPWORDS
STOPWORDS.update(dict((w, 1,) for w in NEW_WORDS))

log = logging.getLogger('reporter')


@cronjobs.register
def cluster():
    # Get all the happy/sad issues in the last week.
    week_ago = datetime.datetime.today() - datetime.timedelta(7)
    now = datetime.datetime.now()
    base_qs = Opinion.objects.filter(locale='en-US', created__gte=week_ago,
                                     version=LATEST_BETAS[FIREFOX])

    log.debug('Beginning clustering')
    cluster_by_feeling(base_qs)
    log.debug('Removing old clusters')
    Theme.objects.filter(created__lt=now).delete()


def cluster_by_feeling(base_qs):
    happy = base_qs.filter(positive=True)
    sad = base_qs.filter(positive=False)
    cluster_by_platform(happy, 'happy')
    cluster_by_platform(sad, 'sad')


def cluster_by_platform(qs, feeling):
    # We need to create corpii for each platform and manually inspect each
    # opinion and put it in the right platform bucket.
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
            dimensions = {
                    'feeling': feeling,
                    'platform': platform.short,
                    }

            # Store the clusters into groups
            for group in result:
                if len(group.similars) < 5:
                    continue

                topic = Theme(**dimensions)
                topic.num_opinions = len(group.similars) + 1
                topic.pivot = group.primary
                topic.save()

                for s in group.similars:
                    Item(theme=topic, opinion=s['object'],
                                score=s['similarity']).save()
