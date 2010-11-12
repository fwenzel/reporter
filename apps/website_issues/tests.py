from nose.tools import eq_
import test_utils

from website_issues import helpers


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
