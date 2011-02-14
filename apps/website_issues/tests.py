import urlparse as urlparse_
from itertools import chain

from nose.tools import eq_, assert_true
import test_utils

from input.urlresolvers import reverse

from website_issues import helpers
from website_issues import utils


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
        def test_without_protocol(self):
            """Test domain extraction from URLs, for HTTP, about:, chrome."""
            test_urls = (
                ('http://www.example.com', 'http://example.com'),
                ('http://example.com', 'http://example.com'),
                ('http://example.com/the/place/to/be', 'http://example.com'),
                ('https://example.net:8080', 'https://example.net:8080'),
                ('https://example.net:8080/abc', 'https://example.net:8080'),
                ('https://me@example.com:8080/xyz', 'https://example.com:8080'),
                ('about:config', 'about:config'),
                ('chrome://something/exciting', 'chrome://something/exciting'),
            )
            for url, expected in test_domains:
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
            eq_(helpers.for_display(domain), expected)

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


class TestViews(test_utils.TestCase):

    def test_invalid_os(self):
        """Bogus os must not confuse us: we are bogus-compatible."""
        r = self.client.get(reverse('website_issues', channel='beta'), 
                            {"os": "bogus"})
        eq_(r.status_code, 200)
        assert_true(len(r.content) > 0)


class TestViews(test_utils.TestCase):

    def test_invalid_platform(self):
        """Bogus platform must not confuse us: we are bogus-compatible."""
        r = self.client.get(reverse('website_issues', channel='beta'),
                            {"platform": "bogus"})
        eq_(r.status_code, 200)
        assert_true(len(r.content) > 0)
