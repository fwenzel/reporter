from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count

from . import APP_IDS, OSES
from .utils import ua_parse, extract_terms, smart_truncate


class OpinionManager(models.Manager):
    def between(self, date_start=None, date_end=None):
        ret = self.get_query_set()
        if date_start:
            ret = ret.filter(created__gte=date_start)
        if date_end:
            ret = ret.filter(created__lte=date_end)
        return ret


class Opinion(models.Model):
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
    locale = models.CharField(max_length=30)

    created = models.DateTimeField(auto_now_add=True)

    objects = OpinionManager()

    class Meta:
        ordering = ('-created',)

    def __unicode__(self):
        return '(%s) "%s"' % (
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
            self.locale = parsed['locale']

        super(Opinion, self).save(*args, **kwargs)

        # Extract terms from description text and save them
        terms = [ t for t in extract_terms(self.description) if
                 len(t) >= settings.MIN_TERM_LENGTH ]
        for term in terms:
            try:
                this_term = Term.objects.get(term=term)
            except Term.DoesNotExist:
                this_term = Term.objects.create(term=term)
            self.terms.add(this_term)


class TermManager(models.Manager):
    def visible(self):
        """All but hidden terms."""
        return self.filter(hidden=False)

    def frequent(self, date_start=None, date_end=None):
        """Frequently used terms in a given timeframe."""
        return self.visible().filter(used_in__in=Opinion.objects.between(
            date_start, date_end)).annotate(cnt=Count('used_in')).order_by(
                '-cnt')


class Term(models.Model):
    """Significant term extraced from description texts."""
    term = models.CharField(max_length=255, unique=True)
    hidden = models.BooleanField(default=False)

    objects = TermManager()

    def __unicode__(self):
        return self.term

    class Meta:
        ordering = ('term',)
