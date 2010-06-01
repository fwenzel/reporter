from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from .utils import ua_parse, extract_terms


class Opinion(models.Model):
    """A single feedback item."""
    positive = models.BooleanField(help_text='Positive/happy sentiment?')
    url = models.URLField(verify_exists=False, blank=True)
    description = models.TextField()
    terms = models.ManyToManyField('Term', related_name='used_in')

    user_agent = models.CharField(max_length=255)
    product = models.PositiveSmallIntegerField()
    version = models.CharField(max_length=30)
    os = models.CharField(max_length=30)
    locale = models.CharField(max_length=30)

    created = models.DateTimeField(auto_now_add=True)

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


class Term(models.Model):
    """Significant term extraced from description texts."""
    term = models.CharField(max_length=255, unique=True)

    def __unicode__(self):
        return self.term
