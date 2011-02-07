from datetime import timedelta

from django.conf import settings
from django.db import models
from django.db.models import Count

import caching.base

from input import OPINION_TYPES, OPINION_PRAISE, RATING_USAGE
from input.models import ModelBase
from input.urlresolvers import reverse

from feedback import APP_IDS, OSES, query
from feedback.utils import ua_parse, extract_terms, smart_truncate


class OpinionManager(caching.base.CachingManager):
    def browse(self, **kwargs):
        """Browse all opinions, restricted by search criteria."""
        opt = lambda x: kwargs.get(x, None)
        # apply complex filters first
        qs = self.between(date_start=opt('date_start'),
                          date_end=opt('date_end'))

        # apply other filters verbatim
        for field in ('type', 'product', 'version', 'locale', 'os'):
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
    type = models.PositiveSmallIntegerField(
            blank=True, default=OPINION_PRAISE.id, db_index=True)
    url = models.URLField(verify_exists=False, blank=True)
    description = models.TextField(blank=True)
    terms = models.ManyToManyField('Term', related_name='used_in')

    user_agent = models.CharField(
        max_length=255, help_text=('Product name etc. are derived from user '
                                   'agent string on save.'))
    product = models.PositiveSmallIntegerField(db_index=True)
    version = models.CharField(max_length=30, db_index=True)
    os = models.CharField(max_length=30, db_index=True)
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
                unicode(OPINION_TYPES[self.type].pretty),
                self.truncated_description)
        except KeyError:  # pragma: no cover
            return unicode(self.type)

    @property
    def truncated_description(self):
        """Shorten opinion for list display etc."""
        return smart_truncate(self.description, length=70)

    @property
    def product_name(self):
        try:
            return APP_IDS[self.product].pretty
        except KeyError:
            return self.product

    @property
    def os_name(self):
        try:
            return OSES[self.os].pretty
        except KeyError:
            return self.os

    def save(self, terms=True, *args, **kwargs):
        # parse UA and stick it into separate fields
        parsed = ua_parse(self.user_agent)
        if parsed:
            self.product = parsed['browser'].id
            self.version = parsed['version']
            self.os = parsed['os']

        new = not self.pk
        super(Opinion, self).save(*args, **kwargs)

        # Extract terms from description text and save them if this is new.
        if new and terms:
            terms = (t for t in extract_terms(self.description) if
                     len(t) >= settings.MIN_TERM_LENGTH)
            for term in terms:
                this_term, created = Term.objects.get_or_create(term=term)
                this_term.save()
                self.terms.add(this_term)

    def get_url_path(self):
        return reverse('opinion.detail', args=(self.id,))


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


class Rating(ModelBase):
    """Ratings associated with an opinion."""
    opinion = models.ForeignKey(Opinion, related_name='ratings')
    type = models.PositiveSmallIntegerField(default=RATING_USAGE[0],
                                            db_index=True)
    value = models.PositiveSmallIntegerField()
