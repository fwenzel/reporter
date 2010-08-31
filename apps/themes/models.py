from django.db import models

from feedback.models import Opinion
from input.models import ModelBase


class Theme(ModelBase):
    pivot = models.ForeignKey(Opinion, related_name='group')
    opinions = models.ManyToManyField(Opinion, through='Item')
    num_opinions = models.IntegerField(default=0, db_index=True)
    feeling = models.CharField(max_length=20, db_index=True)  # happy or sad
    platform = models.CharField(max_length=255, db_index=True)
    created = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        db_table = 'theme'
        ordering = ('-num_opinions', )


class Item(ModelBase):
    theme = models.ForeignKey(Theme, related_name='items')
    opinion = models.ForeignKey(Opinion)
    score = models.FloatField()
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'theme_item'
        ordering = ('-score', )
