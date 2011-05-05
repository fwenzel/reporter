import urlparse as urlparse_

from nose.tools import eq_, assert_true
import test_utils

from input import LATEST_BETAS, FIREFOX, OPINION_PRAISE, OPINION_ISSUE
from input.urlresolvers import reverse
from feedback.models import Opinion

from website_issues import helpers
from website_issues import utils
from website_issues.models import SiteSummary, Cluster, Comment


class TestUtils(test_utils.TestCase):
    def test_urlparse(self):
        """Test urlparser for chrome and about URLs."""

        # about:*
        url = 'about:config'
        p = utils.urlparse(url)
        eq_(p.scheme, 'about')
        eq_(p.netloc, 'config')
        eq_(p.geturl(), url)

        # chrome
        url = 'chrome://somewhere/special'
        p = utils.urlparse(url)
        eq_(p.scheme, 'chrome')
        eq_(p.netloc, 'somewhere')
        eq_(p.path, 'special')
        eq_(p.geturl(), url)

        # HTTP (unchanged from Python)
        url = 'http://example.com/something'
        p = utils.urlparse(url)
        eq_(p, urlparse_.urlparse(url))

    def test_normalize_url(self):
        """Test normalization from urls to sites."""
        test_urls = (
            ('http://www.example.com', 'http://example.com'),
            ('http://example.com', 'http://example.com'),
            ('http://example.com/the/place/to/be', 'http://example.com'),
            ('https://example.net:8080', 'https://example.net:8080'),
            ('https://example.net:8080/abc', 'https://example.net:8080'),
            ('https://me@example.com:8080/xyz', 'https://example.com:8080'),
            ('https://me:pass@example.com:8080/z', 'https://example.com:8080'),
            ('about:config', 'about:config'),
            ('chrome://something/exciting', 'chrome://something/exciting'),
        )
        for url, expected in test_urls:
            eq_(utils.normalize_url(url), expected)


class TestHelpers(test_utils.TestCase):
    def test_url_display(self):
        """Test how HTTP, about:, chrome:// sites are shown to the user"""
        test_domains = (
            ('http://example.com', 'example.com'),
            ('https://example.net:8080/abc', 'example.net:8080'),
            ('about:config', 'about:config'),
            ('chrome://something/exciting', 'chrome://something/exciting'),
        )
        for domain, expected in test_domains:
            eq_(helpers.strip_protocol(domain), expected)

    def test_domain_protocol(self):
        """Test domain extraction from URLs, for HTTP, about:, chrome."""
        test_domains = (
            ('http://example.com', 'http', 'example.com'),
            ('https://example.net:8080/abc', 'https', 'example.net:8080'),
            ('about:config', 'about', 'config'),
            ('chrome://something/exciting', 'chrome', 'something/exciting'),
        )
        for url, protocol, domain in test_domains:
            eq_(helpers.protocol(url), protocol)
            eq_(helpers.domain(url), domain)


NUM_SITES = 2
NUM_PRAISE = 8
NUM_ISSUES = 3


class TestViews(test_utils.TestCase):

    @classmethod
    def setup_class(cls):
        super(TestViews, cls).setup_class()

        def make_comment(cluster, n, i, type):
            "Invent comment i of n for the given cluster."
            o = Opinion(description="Message %i/%i." % (i, n),
                        product=1, version=LATEST_BETAS[FIREFOX],
                        type=type.id, platform='mac', locale='en-US')
            o.save()
            c = Comment(cluster=cluster, description=o.description,
                        opinion_id=o.id, score=1.0)
            c.save()
            return c

        def make_clusters(summary, type, numcomments):
            """Create a bunch of clusters for the given summary."""
            numcreated = 0
            for csize in [NUM_PRAISE - NUM_ISSUES, NUM_ISSUES]:
                if numcreated >= numcomments:
                    break
                cluster = Cluster(site_summary=summary, size=csize)
                for i in xrange(csize):
                    if i == 0:
                        cluster.save()
                    c = make_comment(cluster, csize, i, type)
                    if i == 0:
                        cluster.primary_description = c.description
                        cluster.primary_comment = c
                        cluster.save()
                numcreated += csize

        def make_summaries(siteurl):
            numtotal = NUM_PRAISE + NUM_ISSUES
            defaults = dict(url=siteurl,
                            version=LATEST_BETAS[FIREFOX],
                            positive=True, platform=None)
            all = SiteSummary(size=numtotal, issues_count=NUM_ISSUES,
                              praise_count=NUM_PRAISE, **defaults)
            praise = SiteSummary(size=NUM_PRAISE, issues_count=0,
                                 praise_count=NUM_PRAISE, **defaults)
            issues = SiteSummary(size=NUM_ISSUES, issues_count=NUM_ISSUES,
                                 praise_count=0, **defaults)
            for summary in [all, praise, issues]:
                summary.save()
                make_clusters(summary, OPINION_ISSUE, summary.issues_count)
                make_clusters(summary, OPINION_PRAISE, summary.praise_count)

        for i in xrange(NUM_SITES):
            make_summaries('http://www%i.example.com' % i)

    def setUp(self):
        self.client.get('/')

    def test_sites(self):
        """Quickly check if sites works in general."""
        r = self.client.get(reverse('website_issues'))
        eq_(r.status_code, 200)
        assert_true(len(r.content) > 0)

    def test_single_site(self):
        """Check results for a given site: praise, issues and both."""
        for i in xrange(NUM_SITES):
            for sentiment in ["happy", "sad", None]:
                params = dict(url_='www%i.example.com' % i, protocol='http')
                view_url = reverse('single_site', kwargs=params)
                if sentiment is not None:
                    view_url += '?sentiment=%s' % sentiment
                r = self.client.get(view_url)
                eq_(r.status_code, 200)
                assert_true(len(r.content) > 0)

    def test_nonexistant_site(self):
        """Single site for nonexistent url gives 404."""
        for sentiment in ["happy", "sad", None]:
            params = dict(url_='this.is.nonexistent.com', protocol='http')
            view_url = reverse('single_site', kwargs=params)
            if sentiment is not None:
                view_url += '?sentiment=%s' % sentiment
            r = self.client.get(view_url)
            eq_(r.status_code, 404)
            assert_true(len(r.content) > 0)

    def test_site_theme(self):
        """Check each site theme page."""
        clusters = Cluster.objects.all()
        for c in clusters:
            params = dict(theme_id=c.id)
            r = self.client.get(reverse('site_theme', kwargs=params))
            eq_(r.status_code, 200)
            assert_true(len(r.content) > 0)

    def test_invalid_platform(self):
        """Non-existent platform will not cause an error."""
        r = self.client.get(reverse('website_issues'), {"platform": "bogus"})
        eq_(r.status_code, 200)
        assert_true(len(r.content) > 0)
