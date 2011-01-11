import logging

from celery.decorators import task

from api import cron

log = logging.getLogger('reporter')


@task(rate_limit='1/h')
def export_tsv():
    log.info('Exporting all opinions to TSV!')
    cron.export_tsv()
