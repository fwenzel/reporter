from datetime import datetime, timedelta
from itertools import count
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.db.models import Q
from django.db.models.sql import InsertQuery
from django.db import transaction

from textcluster.cluster import Corpus

from feedback import LATEST_BETAS, FIREFOX, MOBILE, APP_IDS
from feedback.models import Opinion

from website_issues.models import Comment, Cluster, SiteSummary
from website_issues.management.utils import normalize_url
from website_issues.helpers import without_protocol

DB_ALIAS = "website_issues"

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

    The website_issues database can contain multiple entries
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

    option_list = BaseCommand.option_list + (
        make_option('--offline',
                    action='store_true',
                    dest='offline',
                    default=False,
                    help='Output the results as a MySQL dump to stdout rather'
                         'than loading them into the sites database.'),
    )

    @transaction.commit_manually
    def handle(self, *args, **options):
        # forwards compatible with django dev
        try:
            err = self.stderr.write
            out = self.stdout.write
        except AttributeError:
            import sys
            err = sys.stderr.write
            out = sys.stdout.write

        # Pregroup comments by key criteria.
        self.collect_groups(err)

        err("Pregenerating positive/negative counts...\n")
        SiteGroup.calculate_positive_counts()

        # Generate IDs without hitting the database
        self.site_summary_id = count(1)
        self.cluster_id = count(1)
        self.comment_id = count(1)

        err("Sorting...\n")
        sorted_sites = SiteGroup.sorted(err)

        err("Generating clusters...\n")
        context = MysqlDumpStorage(err, out) if options['offline'] \
                                             else DatabaseStorage(err)
        with context as storage:
            for i, group in enumerate(sorted_sites):
                self.generate_clusters_for(err, storage, group)
                # The first clusters take longest, report more often
                if i < 100 or i % 100 == 99:
                    err("...generated clusters for %i summaries\n" % (i+1))
        err("Generated clusters for %i site summaries.\n"
            % self.site_summary_id.next())

    def collect_groups(self, err):
        now = datetime.now()
        seven_days_ago = now - timedelta(days=7)
        one_day_ago = now - timedelta(days=1)
        latest_versions = (LATEST_BETAS[FIREFOX], LATEST_BETAS[MOBILE])
        err("Collecting groups...\n")
        def add(opinion, **kwargs):
            """Add this opinion to it's summary group."""
            return SiteGroup.get(frozendict(kwargs)).add(opinion.pk)

        def add_variants(opinion, **keypart):
            """Add variants for "positive" and "os" set/ignored."""
            add(opinion, os=opinion.os, positive=opinion.positive, **keypart)
            add(opinion, os=opinion.os, positive=None,             **keypart)
            # These will probably not be read anymore with 1.9 in production.
            add(opinion, os=None,       positive=opinion.positive, **keypart)
            add(opinion, os=None,       positive=None,             **keypart)
            # These are for 1.9+ and allow siphoning by product.
            app = '<%s>' % APP_IDS[opinion.product].short
            add(opinion, os=app,        positive=opinion.positive, **keypart)
            add(opinion, os=app,        positive=None,             **keypart)


        queryset = Opinion.objects.filter(
                       ~Q(url__exact="") & (
                           Q(created__range=(seven_days_ago, now))
                           | Q(version__in=latest_versions)
                       )
                   ).only("url", "version", "created", "positive", "os")

        i = 0
        for i, opinion in enumerate(queryset):
            site_url = normalize_url(opinion.url)
            if opinion.version in latest_versions:
                add_variants(opinion, version=opinion.version, url=site_url)
            if opinion.created > seven_days_ago:
                add_variants(opinion, version="<week>", url=site_url)
                if opinion.created > one_day_ago:
                    add_variants(opinion, version="<day>", url=site_url)

            if i % 1000 == 0: err("    ... %i comments\n" % i)
        err("%i site summaries for %i comments.\n" % (len(SiteGroup.all), i))

    def add_singleton_cluster(self, storage, site_summary, opinion):
        cluster = Cluster(pk=self.cluster_id.next(),
                          site_summary=site_summary,
                          primary_description=opinion.description,
                          primary_comment=None,
                          positive=opinion.positive,
                          size=1)
        storage.save(cluster)
        comment = Comment(pk=self.comment_id.next(),
                          description=opinion.description,
                          opinion_id=opinion.id,
                          cluster=cluster,
                          score=1.0)
        storage.save(comment)
        cluster.primary_comment = comment
        storage.save(cluster)

    def generate_clusters_for(self, err, storage, group):
        num_clusters = 0
        site_summary = SiteSummary(pk=self.site_summary_id.next(),
                                   size=len(group.opinion_pks),
                                   issues_count=group.positive_counts[0],
                                   praise_count=group.positive_counts[1],
                                   **group.key)
        storage.save(site_summary)
        group_positive = group.key["positive"]

        # Handle single-comment case:
        if site_summary.size == 1:
            opinion = Opinion.objects.get(pk=group.opinion_pks[0])
            self.add_singleton_cluster(storage, site_summary, opinion)
            return

        opinions = Opinion.objects.filter(pk__in=group.opinion_pks)

        # Handle cluster case, make one corpus for positive, one for negative.
        for positive in (0,1):
            if group_positive is not None and positive != group_positive:
                continue
            corpus = Corpus()
            remaining_opinions = { }
            for opinion in opinions:
                if opinion.positive != positive: continue
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
                                  primary_comment=None,
                                  positive=positive,
                                  size=len(comments))
                storage.save(cluster)
                for comment in comments:
                    del remaining_opinions[comment.opinion_id]
                    comment.cluster = cluster
                    storage.save(comment)
                cluster.primary_comment=comments[0]
                cluster.save()

            # Add singletons for remaining opinions
            for opinion in remaining_opinions.values():
                self.add_singleton_cluster(storage, site_summary, opinion)


class MysqlDumpStorage(object):
    """Storage that dumps objects into MySQL syntax insert statements.

    These are probably going to be compatible with most database
    implementations.  We need to access the MySQL driver directly because
    django does not expose an API for escaping parameters using the configured
    database connection.
    """
    def __init__(self, err, out):
        self.err = err
        self.out = out
        # We need entirely different imports if this storage is used.
        from django.db import connections
        from MySQLdb import connect
        self.connection = connections[DB_ALIAS]
        db = settings.DATABASES[DB_ALIAS]
        connection = connect(db=db["NAME"], host=db["HOST"], user=db["USER"],
                             passwd=db["PASSWORD"], charset="utf8",
                             use_unicode=True)
        self.mysql_escape_string = connection.escape_string
        self.out("""
        /*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
        /*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
        /*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
        /*!40101 SET NAMES utf8 */;
        /*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
        /*!40103 SET TIME_ZONE='+00:00' */;
        /*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
        /*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
        /*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
        /*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;
        """)

    def __enter__(self):
        return self

    def __exit__(self, type, value, traceback):
        if type is not None:
            self.err("Unexpected error occurred. Re-raising.")
            return False
        self.out("""
        /*!40000 ALTER TABLE `website_issues_sitesummary` ENABLE KEYS */;
        UNLOCK TABLES;
        /*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

        /*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
        /*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
        /*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
        /*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
        /*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
        /*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
        /*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
        """)

    def placeholder(self, field, val):
        """Copied from the django query compiler (private api)."""
        if field is None:
            # A field value of None means the value is raw.
            return val
        elif hasattr(field, 'get_placeholder'):
            # Some fields (e.g. geo fields) need special munging before
            # they can be inserted.
            return field.get_placeholder(val, self.connection)
        else:
            # Return the common case for the placeholder
            return '%s'

    def escape(self, v):
        """Encode value to utf-8 and escape it for MySQL insertion."""
        escape = self.mysql_escape_string
        if v is None: return "NULL"
        elif type(v) == unicode: return "'%s'" % escape(v.encode("utf-8"))
        elif type(v) == str: return "'%s'" % escape(v)
        elif type(v) in (bool, int, float): return "%s" % v
        return "'%s'" % escape(str(v))

    def quote(self, name):
        """Encode value to utf-8 and quote it as a MySQL name."""
        return self.connection.ops.quote_name(name)

    def save(self, model):
        """Adapted from the django query compiler (private api)."""
        if isinstance(model, Cluster) and model.primary_comment is None:
            return
        query = InsertQuery(model)
        meta = query.model._meta
        values = [(f, f.get_db_prep_save(f.pre_save(model, True),
                  connection=self.connection))
                  for f in meta.local_fields]
        query.insert_values(values)
        result = [
            'INSERT INTO %s' % self.quote(meta.db_table),
            '(%s)' % ', '.join([self.quote(c) for c in query.columns]),
            "VALUES (%s)" % ", ".join([self.escape(p) for p in query.params])
        ]
        self.out(' '.join(result))
        self.out(";\n")


class DatabaseStorage(object):
    """Storage context that saves new model objects.

    This storage inserts the objects into the database configured for their
    model, replacing the current contents in one transaction.

    For offline processing, use MysqlDumpStorage instead which is *much*
    faster, as currently as DatabaseStorage needs one read and one write for
    every save, even with the pregenerated PK."""

    def __init__(self, err):
        self.err = err

    def __enter__(self):
        self.err("Deleting existing objects...\n")
        # the delete cascades
        SiteSummary.objects.all().delete()
        return self

    def __exit__(self, type, value, traceback):
        if type is not None:
            self.err("Unexpected error occurred. Rolling back, re-raising.\n")
            transaction.rollback()
            return False
        transaction.commit()

    def save(self, model):
        model.save()


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
