import logging

from celery.decorators import task

from themes.cron import cluster

log = logging.getLogger('reporter')


@task(rate_limit='1/h')
def recluster():
    log.info('Clustering!')
    cluster()
