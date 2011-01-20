from django.db import models

import caching.base


class ModelBase(caching.base.CachingMixin, models.Model):
    """Common base model for all models: Implements caching."""

    objects = caching.base.CachingManager()

    class Meta:
        abstract = True
