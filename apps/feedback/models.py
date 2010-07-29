from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Count
from django.db.models.query import QuerySet

import caching.base

from input.urlresolvers import reverse
from . import APP_IDS, OSES, query
from .utils import ua_parse, extract_terms, smart_truncate


class ModelBase(caching.base.CachingMixin, models.Model):
    """Common base model for all models: Implements caching."""

    objects = caching.base.CachingManager()

    class Meta:
        abstract = True


class OpinionManager(caching.base.CachingManager):
    def browse(self, **kwargs):
        """Browse all opinions, restricted by search criteria."""
        opt = lambda x: kwargs.get(x, None)
        # apply complex filters first
        qs = self.between(date_start=opt('date_start'),
                          date_end=opt('date_end'))
        if opt('positive'):
            qs = qs.filter(positive=opt('positive'))

        # apply other filters verbatim
        for field in ('product', 'version', 'locale', 'os'):
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
    positive = models.BooleanField(help_text='Positive/happy sentiment?')
    url = models.URLField(verify_exists=False, blank=True)
    description = models.TextField()
    terms = models.ManyToManyField('Term', related_name='used_in')

    user_agent = models.CharField(
        max_length=255, help_text=('Product name etc. are derived from user '
                                   'agent string on save.'))
    product = models.PositiveSmallIntegerField()
    version = models.CharField(max_length=30)
    os = models.CharField(max_length=30)
    locale = models.CharField(max_length=30, blank=True)

    created = models.DateTimeField(auto_now_add=True)

    objects = OpinionManager()

    class Meta:
        ordering = ('-created',)

    def __unicode__(self):
        return '(%s) %s' % (
            self.positive and '+' or '-',
            self.truncated_description)

    @property
    def truncated_description(self):
        """Shorten opinion for list display etc."""
        return smart_truncate(self.description, length=70)

    @property
    def product_name(self):
        try:
            return APP_IDS[self.product].pretty
        except IndexError:
            return self.product

    @property
    def os_name(self):
        try:
            return OSES[self.os].pretty
        except IndexError:
            return self.os

    def save(self, *args, **kwargs):
        # parse UA and stick it into separate fields
        parsed = ua_parse(self.user_agent)
        if parsed:
            self.product = parsed['browser'].id
            self.version = parsed['version']
            self.os = parsed['os']

        super(Opinion, self).save(*args, **kwargs)

        # Extract terms from description text and save them
        terms = [t for t in extract_terms(self.description) if
                 len(t) >= settings.MIN_TERM_LENGTH]
        for term in terms:
            try:
                this_term = Term.objects.get(term=term)
            except Term.DoesNotExist:
                this_term = Term.objects.create(term=term)
            self.terms.add(this_term)


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
                    params['used_in__'+field] = kwargs[field]

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


class ClusterType(ModelBase):
    """A single type of cluster.  E.g. weekly_happy, weekly_sad."""
    feeling = models.CharField(max_length=20)  # happy or sad
    platform = models.CharField(max_length=255)
    version = models.CharField(max_length=255)
    frequency = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)

    def get_url_path(self):
        args = [self.feeling, self.platform, self.version, self.frequency]
        return reverse('cluster', args=args)

    class Meta:
        unique_together = (("feeling", "platform", "version", "frequency"),)


class Cluster(ModelBase):
    type = models.ForeignKey(ClusterType, db_index=True,
                             related_name='clusters')
    pivot = models.ForeignKey(Opinion, related_name='clusters')
    opinions = models.ManyToManyField(Opinion, through='ClusterItem')
    num_opinions = models.IntegerField(default=0, db_index=True)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-num_opinions', )


class ClusterItem(ModelBase):
    cluster = models.ForeignKey(Cluster)
    opinion = models.ForeignKey(Opinion)
    score = models.FloatField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ('-score', )
