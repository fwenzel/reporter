from django.db import models


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


class Term(models.Model):
    """Significant term extraced from description texts."""
    term = models.CharField(max_length=255, unique=True)
