from datetime import datetime, timedelta
from itertools import count

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db.models import Q
from django.db import transaction

from textcluster.cluster import Corpus

from feedback.models import Opinion
from product_details import firefox_versions as versions

from website_issues.models import Comment, Cluster, SiteSummary
from website_issues.management.utils import normalize_url
from website_issues.helpers import without_protocol


class Command(BaseCommand):
    """
    Build per-site, per-ve=rsion clusters from the opininions in the
    database.  A logical site is a set of all urls with the same
    "normalized" form:
      http://xm.pl/search/x, http://www.exam.pl/ -> http://xm.pl
      https://xm.pl/mail, https://exam.pl/mail   -> https://xm.pl
      https://mail.xm.pl, https://mail.xm.pl/y   -> https://mail.xm.pl

    Whenever a user views the sites dashboard, each logical site will
    either occur exactly once in the listing, or not at all --
    depending on whether there are comments matching the search
    criteria.

    The websites_issues database can contain multiple entries
    ("summaries") for each logical site: one for each combinations of
    search criteria that yields a result.  Along with the criteria, the
    number of matching comments is stored.

    Individual comments can match multiple criteria and thus be
    associated to multiple site summaries.  For example, all comments
    match "positive IS NULL" (means: don't care about positive), so
    they are listed for that site summary as well as for the site
    summary that selects their positive.

    Site summaries are sorted descending by the amount of comments that
    belong to them, then ascending by their normalized URL.  That
    allows for efficient querying, as the DBMS can walk the index (or
    even the table) and stop when a sufficient number has been found,
    knowing there will be no larger results that need to go on top.

    Example:
    Suppose there are two logical sites, "http://a.com" (A) and
    "http://b.com" (B), where A has more overall feedback, but B has
    the most negative feedback.  Also, there is a tiny site with one
    comment from last week:

    id | version | positive | size | url
     1 | 4.0b1   | NULL     | 999  | http://a.com
     3 | 4.0b1   | 1        | 800  | http://a.com
     2 | 4.0b1   | NULL     | 500  | http://b.com
     4 | 4.0b1   | 1        | 250  | http://b.com
     5 | 4.0b1   | 0        | 250  | http://b.com
     6 | 4.0b1   | 0        | 199  | http://a.com
     7 | <week>  | NULL     | 1    | http://tiny.com
     8 | <week>  | 0        | 1    | http://tiny.com

    The actual clusters are inserted in order of and indexed by their
    site.
    """

    @transaction.commit_manually
    def handle(self, *args, **options):
        # forwards compatible with django dev
        try:
            err = self.stderr.write
        except AttributeError:
            import sys
            err = sys.stderr.write

        # Pregroup comments by key criteria.
        self.collect_groups(err)

        err("Pregenerating positive/negative counts...\n")
        SiteGroup.calculate_positive_counts()

        # Cascades to clusters and comments.
        SiteSummary.objects.all().delete()

        # Generate IDs without hitting the database
        self.site_summary_id = count()
        self.cluster_id = count()
        self.comment_id = count()

        err("Generating clusters...\n")
        try:
            for i, group in enumerate(SiteGroup.sorted(err)):
                if i % 200 == 0:
                    err("...generated clusters for %i site summaries.\n" % i)
                self.generate_clusters_for(err, group)
        except:
            err("An unexpected error occurred. Rolling back. Re-raising.\n")
            transaction.rollback()
            raise
        else: transaction.commit()
        err("Generated clusters for %i site summaries.\n"
            % self.site_summary_id.next())

    def collect_groups(self, err):
        now = datetime.now()
        seven_days_ago = now - timedelta(days=7)
        latest_version = versions["LATEST_FIREFOX_DEVEL_VERSION"]
        err("Collecting groups...\n")
        def add(opinion, **kwargs):
            return SiteGroup.get(frozendict(kwargs)).add(opinion.pk)
        queryset = Opinion.objects.filter(
                       ~Q(url__exact="") & (
                           Q(created__range=(seven_days_ago, now))
                           | Q(version__exact=latest_version)
                       )
                   ).only("url", "version", "created", "positive")
        for i, opinion in enumerate(queryset):
            site_url = normalize_url(opinion.url)
            if opinion.version == latest_version:
                keypart = dict(version=opinion.version, url=site_url)
                add(opinion, positive=opinion.positive, **keypart)
                add(opinion, positive=None, **keypart)
            if opinion.created > seven_days_ago:
                keypart = dict(version="<week>", url=site_url)
                add(opinion, positive=opinion.positive, **keypart)
                add(opinion, positive=None, **keypart)
            if i % 1000 == 0: err("    ... %i comments\n" % i)
        err("%i site summaries for %i comments.\n" % (len(SiteGroup.all), i))


    def add_singleton_cluster(self, site_summary, opinion):
        comment = Comment(pk=self.comment_id.next(),
                          description=opinion.description,
                          opinion_id=opinion.id,
                          score=1.0)
        cluster = Cluster(pk=self.cluster_id.next(),
                          site_summary=site_summary,
                          primary_description=comment.description,
                          primary_comment=comment,
                          size=1)
        cluster.save()
        comment.cluster = cluster
        comment.save()

    def generate_clusters_for(self, err, group):
        num_clusters = 0
        site_summary = SiteSummary(pk=self.site_summary_id.next(),
                                   size=len(group.opinion_pks),
                                   issues_count=group.positive_counts[0],
                                   praise_count=group.positive_counts[1],
                                   **group.key)
        site_summary.save()

        # Handle single-comment case:
        if site_summary.size == 1:
            opinion = Opinion.objects.get(pk=group.opinion_pks[0])
            self.add_singleton_cluster(site_summary, opinion)
            return

        # Handle cluster case:
        corpus = Corpus()
        remaining_opinions = { }
        for opinion in Opinion.objects.filter(pk__in=group.opinion_pks):
            remaining_opinions[opinion.id] = opinion
            corpus.add(opinion, str=unicode(opinion.description))
        clusters = corpus.cluster()
        for next in clusters:
            primary = {"object": next.primary, "similarity": 1.0}
            comments = [Comment(pk=self.comment_id.next(),
                                description=doc["object"].description,
                                opinion_id=doc["object"].id,
                                score=doc["similarity"])
                        for doc in [primary] + next.similars]
            cluster = Cluster(pk=self.cluster_id.next(),
                              site_summary=site_summary,
                              primary_description=comments[0].description,
                              primary_comment=comments[0],
                              size=len(comments))
            cluster.save()
            for comment in comments:
                del remaining_opinions[comment.opinion_id]
                comment.cluster = cluster
                comment.save()

        # Add singletons for remaining opinions
        for opinion in remaining_opinions.values():
            self.add_singleton_cluster(site_summary, opinion)


class frozendict(dict):
    def __setitem__(self, key, value): pass
    def __hash__(self):
        items = self.items()
        h = 0
        for item in items: h ^= hash(item)
        return h


class SiteGroup(object):
    """A group has an immutable key part and a mutable list of associated
       objects (opinions).
    """

    all = {}

    @classmethod
    def get(cls, key):
        if key not in cls.all: cls.all[key] = cls(key)
        return cls.all[key]

    @classmethod
    def sorted(cls, err):
        sortkey = lambda group: (-len(group.opinion_pks),
                                 without_protocol(group.key["url"]))
        res = sorted(cls.all.itervalues(), key=sortkey)
        return res

    @classmethod
    def calculate_positive_counts(cls):
        """Update the issues/praises counts used by the dashboard."""
        for key, src in cls.all.iteritems():
            if key["positive"] is None: continue
            keyparams = dict(**key)
            for positive_setting in (False, True, None):
                keyparams["positive"] = positive_setting
                try: dest = cls.all[frozendict(**keyparams)]
                except KeyError: continue
                dest.positive_counts[key["positive"]] = len(src.opinion_pks)

    def __init__(self, key):
        self.key = key
        self.opinion_pks = []
        self.positive_counts = [0, 0]

    def add(self, opinion_pk):
        self.opinion_pks.append(opinion_pk)
