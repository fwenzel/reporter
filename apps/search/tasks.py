from celeryutils import task

from feedback.models import Opinion
from elasticutils import get_es, es_required


@task
@es_required
def add_to_index(pks, es, **kw):
    for opinion in Opinion.objects.filter(pk__in=pks):
        opinion.update_index(bulk=True)
    es.force_bulk()
