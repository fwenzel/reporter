from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Count
from django.db.models.query import QuerySet

import caching.base

from . import APP_IDS, OSES, query
from .utils import ua_parse, extract_terms, smart_truncate


class ModelBase(caching.base.CachingMixin, models.Model):
    """Common base model for all models: Implements caching."""

    objects = caching.base.CachingManager()

    class Meta:
        abstract = True


class OpinionManager(models.Manager):
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
            self.locale = parsed['locale'] or ''

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
        return QuerySet(self.model, using=self._db,
                        query=query.InnerQuery(self.model))

    def visible(self):
        """All but hidden terms."""
        return self.filter(hidden=False)

    def frequent(self, opinions=None, date_start=None, date_end=None):
        """Frequently used terms in a given timeframe."""
        # Either you feed in opinions or a date range. Not both.
        assert(not (opinions and (date_start or date_end)))

        terms = self.visible()
        if opinions:
            terms = terms.filter(used_in__in=opinions)
        elif date_start or date_end:
            terms = terms.filter(used_in__in=Opinion.objects.between(
                date_start, date_end))
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
