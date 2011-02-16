from django.db import models

import caching.base

from input.models import ModelBase
from input.urlresolvers import reverse
from input.decorators import cached_property

from website_issues import helpers
from website_issues import utils


class Comment(ModelBase):
    """Comments and their grouping to a cluster."""
    cluster = models.ForeignKey("Cluster", related_name="comments")
    description = models.TextField()
    opinion_id = models.PositiveIntegerField()
    score = models.FloatField()

    class Meta:
        ordering = ['-score']


class Cluster(ModelBase):
    """Summary information per cluster."""
    site_summary = models.ForeignKey("SiteSummary", related_name="clusters")
    size = models.PositiveIntegerField()
    primary_description = models.TextField()
    primary_comment = models.ForeignKey("Comment",
                                        null=True,
                                        related_name="defined_cluster")
    positive = models.BooleanField(default=False)

    class Meta:
        ordering = ['-size']

    @cached_property
    def secondary_comments(self):
        qs = self.comments.exclude(pk=self.primary_comment.pk)
        return qs

    def get_absolute_url(self):
        return reverse('site_theme', args=[self.pk])


class QuerySetManager(caching.base.CachingManager):
    """Manager that allows to use a subclass of QuerySet."""
    def __init__(self, qs_class=models.query.QuerySet):
        self.queryset_class = qs_class
        super(QuerySetManager, self).__init__()

    def get_query_set(self):
        return self.queryset_class(self.model)


class SiteSummaryQuerySet(caching.base.CachingQuerySet):
    """Queryset that prefetches related objects as soon as DB is hit.

    Also uses caching to get the selected objects (Unfortunately Django
    ORM does not fetch related objects along reverse ManyToOne/ForeignKey
    relations).
    When fetching n sites this will result in two queries instead
    of n+1 queries.
    """

    def iterator(self):
        """Get selected sites with clusters transparently populated."""
        lookup = {}
        objects = []
        for obj in super(SiteSummaryQuerySet, self).iterator():
            obj.all_clusters = []
            objects.append(obj)
            lookup[obj.pk] = obj

        clusters = Cluster.objects.filter(
            site_summary__id__in=[obj.pk for obj in objects]
        )
        for cluster in clusters:
            lookup[cluster.site_summary_id].all_clusters.append(cluster)
        for obj in objects:
            yield obj


class SiteSummary(ModelBase):
    """Summary information per site (url x version x positive)."""
    url = models.URLField(verify_exists=False, blank=True)
    version = models.CharField(max_length=30)
    positive = models.NullBooleanField()
    platform = models.CharField(max_length=30, null=True)
    size = models.PositiveIntegerField()
    issues_count = models.PositiveIntegerField()
    praise_count = models.PositiveIntegerField()

    objects = QuerySetManager(SiteSummaryQuerySet)

    _clusters = None

    def _get_clusters(self):
        # recover in case someone else than objects.iterator instantiated self
        if self._clusters is None: self._clusters = list(self.clusters.all())
        return self._clusters

    def _set_clusters(self, clusters):
        self._clusters = clusters

    all_clusters = property(_get_clusters, _set_clusters)

    class Meta:
        # This ordering is already established when the table is created:
        # ordering = ['-size', 'url']
        #
        # Specifying it manually will slow down the vast majority of queries
        # considerably (sorting everything instead of doing a head-scan over
        # the table, which is bad as our indices' cardinality is low), because
        # InnoDB only recognizes PKs/UNIQUE columns for pre-ordering.
        #
        # This comment exists so that the ordering is not added in the future.
        pass

    @cached_property
    def parsed_url(self):
        return utils.urlparse(self.url)

    @cached_property
    def protocol(self):
        return helpers.protocol(self.url)

    @cached_property
    def domain(self):
        return helpers.domain(self.url)

    def get_absolute_url(self):
        return reverse('single_site', args=[self.protocol, self.domain])
