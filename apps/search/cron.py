import commonware.log
import cronjobs
from celery.messaging import establish_connection
from celeryutils import chunked

import input
from feedback.models import Opinion
from search import tasks

log = commonware.log.getLogger('i.cron')


@cronjobs.register
def index_all():
    """
    This reindexes all the Opinions in usage.  This is not intended to be run
    other than to initially seed Elastic Search.
    """
    ids = (Opinion.objects
           .filter(_type__in=[i.id for i in input.OPINION_USAGE])
           .values_list('id', flat=True))
    with establish_connection() as conn:
        for chunk in chunked(ids, 1000):
            tasks.add_to_index.apply_async(args=[chunk], connection=conn)
