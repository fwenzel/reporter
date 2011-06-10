from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Count, signals

import caching.base
import commonware
from elasticutils import es_required
from pyes import djangoutils
from pyes.exceptions import NotFoundException as PyesNotFoundException

from feedback import query, utils
from feedback.utils import ua_parse, extract_terms, smart_truncate
from input import PRODUCT_IDS, OPINION_TYPES, OPINION_PRAISE, PLATFORMS
from input.models import ModelBase
from input.urlresolvers import reverse

log = commonware.log.getLogger('feedback')


class OpinionManager(caching.base.CachingManager):
    def browse(self, **kwargs):
        """Browse all opinions, restricted by search criteria."""
        opt = lambda x: kwargs.get(x, None)
        # apply complex filters first
        qs = self.between(date_start=opt('date_start'),
                          date_end=opt('date_end'))

        # apply other filters verbatim
        for field in ('type', 'product', 'version', 'locale', 'platform'):
            if opt(field):
                qs = qs.filter(**{field: opt(field)})

        return qs

    def between(self, date_start=None, date_end=None):
        ret = self.get_query_set()
        if date_start:
            ret = ret.filter(created__gte=date_start)
        if date_end:
            ret = ret.filter(created__lt=date_end + timedelta(days=1))
        return ret


class Opinion(ModelBase):
    """A single feedback item."""
    _type = models.PositiveSmallIntegerField(blank=True,
        db_column='type', default=OPINION_PRAISE.id, db_index=True)

    url = models.URLField(verify_exists=False, blank=True)
    description = models.TextField(blank=True)
    terms = models.ManyToManyField('Term', related_name='used_in')

    user_agent = models.CharField(
        max_length=255, help_text=('Product name etc. are derived from user '
                                   'agent string on save.'))
    product = models.PositiveSmallIntegerField(db_index=True)
    version = models.CharField(max_length=30, db_index=True)
    platform = models.CharField(max_length=30, db_index=True)
    locale = models.CharField(max_length=30, blank=True, db_index=True)

    # Mobile device information
    manufacturer = models.CharField(max_length=255, blank=True, db_index=True)
    device = models.CharField(max_length=255, blank=True, db_index=True)

    created = models.DateTimeField(auto_now_add=True, db_index=True)

    objects = OpinionManager()

    class Meta:
        ordering = ('-created',)

    def __unicode__(self):
        try:
            return u'(%s) %s' % (
                unicode(OPINION_TYPES[self._type].pretty),
                self.truncated_description)
        except KeyError:  # pragma: no cover
            return unicode(self._type)

    @property
    def truncated_description(self):
        """Shorten opinion for list display etc."""
        return smart_truncate(self.description, length=70)

    @property
    def product_name(self):
        try:
            return PRODUCT_IDS[self.product].pretty
        except KeyError:
            return self.product

    @property
    def platform_name(self):
        try:
            return PLATFORMS[self.platform].pretty
        except KeyError:
            return self.platform

    @property
    def type(self):
        """
        Return a type object with id, short name, and localized/pretty
        name properties.
        """
        return OPINION_TYPES[self._type]

    def get_url_path(self):
        return reverse('opinion.detail', args=(self.id,))

    @es_required
    def update_index(self, es, bulk=False):
        data = djangoutils.get_values(self)
        try:
            es.index(data, settings.ES_INDEX, 'opinion', self.id, bulk=bulk)
        except Exception, e:
            log.error("ElasticSearch errored for opinion (%s): %s" % (self, e))
        else:
            log.debug('Opinion %d added to search index.' % self.id)

    @es_required
    def remove_from_index(self, es, bulk=False):
        try:
            es.delete(settings.ES_INDEX, 'opinion', self.id, bulk=bulk)
        except PyesNotFoundException:
            pass
        except Exception, e:
            log.error("ElasticSearch error removing opinion (%s): %s" %
                      (self, e))
        else:
            log.debug('Opinion %d removed from search index.' % self.id)


def parse_user_agent(sender, instance, **kw):
    parsed = ua_parse(instance.user_agent)
    if parsed:
        instance.product = parsed['browser'].id
        instance.version = parsed['version']
        instance.platform = parsed['platform']


# TODO: add this to celery
def extract_terms(sender, instance, **kw):
    if instance.terms.all() or settings.DISABLE_TERMS:
        return
    terms = (t for t in utils.extract_terms(instance.description) if
             len(t) >= settings.MIN_TERM_LENGTH)
    for term in terms:
        this_term, created = Term.objects.get_or_create(term=term)
        instance.terms.add(this_term)

def post_to_elastic(sender, instance, **kw):
    """Asynchronously update the opinion in ElasticSearch."""
    from search import tasks
    tasks.add_to_index.delay([instance.id])

signals.pre_save.connect(parse_user_agent, sender=Opinion)
signals.post_save.connect(extract_terms, sender=Opinion,
                          dispatch_uid='extract_terms')
signals.post_save.connect(post_to_elastic, sender=Opinion)

unindex_opinion = lambda instance, **kwargs: instance.remove_from_index()
signals.post_delete.connect(unindex_opinion, sender=Opinion)

# post_Save for POST to metrics

class TermManager(models.Manager):
    def get_query_set(self):
        """Use a query that won't use left joins."""
        return caching.base.CachingQuerySet(
            self.model, using=self._db, query=query.InnerQuery(self.model))

    def visible(self):
        """All but hidden terms."""
        return self.filter(hidden=False)

    def frequent(self, opinions=None, date_start=None, date_end=None,
                 **kwargs):
        """Frequently used terms in a given timeframe."""
        terms = self.visible()
        if opinions:
            terms = terms.filter(used_in__in=opinions)
        else:
            params = {}
            if date_start:
                params['used_in__created__gte'] = date_start
            if date_end:
                params['used_in__created__lt'] = (
                    date_end + timedelta(days=1))
            # Allow filtering by any opinion field in kwargs
            for field in (f.name for f in Opinion._meta.fields):
                if kwargs.get(field):
                    params['used_in__' + field] = kwargs[field]

            if params:
                terms = terms.filter(**params)

        terms = terms.annotate(cnt=Count('used_in')).order_by('-cnt')
        return terms


class Term(ModelBase):
    """Significant term extraced from description texts."""
    term = models.CharField(max_length=255, unique=True)
    hidden = models.BooleanField(default=False)

    objects = TermManager()

    def __unicode__(self):
        return self.term

    class Meta:
        ordering = ('term',)
