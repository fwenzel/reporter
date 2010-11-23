import urlparse as urlparse_

from nose.tools import eq_
import test_utils

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


class TestHelpers(test_utils.TestCase):
    def test_without_protocol(self):
        """Test domain extraction from URLs, for HTTP, about:, chrome."""
        test_domains = (
            ('http://example.com', 'example.com'),
            ('https://www.example.net:8080/abc', 'www.example.net:8080'),
            ('about:config', 'about:config'),
            ('chrome://something/exciting', 'chrome://something/exciting'),
        )
        for domain, expected in test_domains:
            eq_(helpers.without_protocol(domain), expected)
