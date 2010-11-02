from datetime import datetime

from django import http
from django.conf import settings
from django.core.exceptions import ValidationError
from django.test import TestCase
from input.urlresolvers import reverse

from nose.tools import eq_
from product_details import product_details

from . import FIREFOX, MOBILE
from .utils import detect_language, ua_parse, smart_truncate
from .validators import validate_no_urls, ExtendedURLValidator
from .version_compare import simplify_version


class UtilTests(TestCase):
    def test_ua_parse(self):
        """Test user agent parser for Firefox."""
        patterns = (
            # valid Fx
            ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; de; rv:1.9.2.3) '
             'Gecko/20100401 Firefox/3.6.3',
             FIREFOX, '3.6.3', 'mac'),
            ('Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.4) '
             'Gecko/20100611 Firefox/3.6.4 (.NET CLR 3.5.30729)',
             FIREFOX, '3.6.4', 'winxp'),
            # additional parentheses (bug 578339)
            ('Mozilla/5.0 (X11; U; Linux i686 (x86_64); en-US; rv:2.0b1) '
             'Gecko/20100628 Firefox/4.0b1',
             FIREFOX, '4.0b1', 'linux'),
            # locale fallback (bug 578339)
            ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; fr-FR; rv:2.0b1) '
             'Gecko/20100628 Firefox/4.0b1',
             FIREFOX, '4.0b1', 'mac'),
            ('Mozilla/5.0 (X11; U; Linux x86_64; cs-CZ; rv:2.0b2pre) Gecko/20100630 '
             'Minefield/4.0b2pre',
             FIREFOX, '4.0b2pre', 'linux'),

            # valid Fennec
            ('Mozilla/5.0 (X11; U; Linux armv6l; fr; rv:1.9.1b1pre) Gecko/'
             '20081005220218 Gecko/2008052201 Fennec/0.9pre',
             MOBILE, '0.9pre', 'linux'),
            ('Mozilla/5.0 (X11; U; FreeBSD; en-US; rv:1.9.2a1pre) '
             'Gecko/20090626 Fennec/1.0b2',
             MOBILE, '1.0b2', 'other'),
            ('Mozilla/5.0 (Maemo; Linux armv71; rv:2.0b6pre) Gecko/'
             '20100924 Namoroka/4.0b7pre Fennec/2.0b1pre',
             MOBILE, '2.0b1pre', 'maemo'),
            ('Mozilla/5.0 (Android; Linux armv71; rv:2.0b6pre) Gecko/'
             '20100924 Namoroka/4.0b7pre Fennec/2.0b1pre',
             MOBILE, '2.0b1pre', 'android'),

            # invalid
            ('A completely bogus Firefox user agent string.', None),
            ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; en-us) '
             'AppleWebKit/531.22.7 (KHTML, like Gecko) Version/4.0.5 '
             'Safari/531.22.7', None),
        )

        for pattern in patterns:
            parsed = ua_parse(pattern[0])
            if pattern[1]:
                self.assertEquals(parsed['browser'], pattern[1])
                self.assertEquals(parsed['version'], pattern[2])
                self.assertEquals(parsed['os'], pattern[3])
            else:
                self.assert_(parsed is None)

    def test_detect_language(self):
        """Check Accept-Language matching for feedback submission."""
        patterns = (
            ('en-us,en;q=0.7,de;q=0.8', 'en-US'),
            ('fr-FR,de-DE;q=0.5', 'fr'),
            ('zh, en-us;q=0.8, en;q=0.6', 'en-US'),
            ('German', ''), # invalid
        )

        for pattern in patterns:
            req = http.HttpRequest()
            req.META['HTTP_ACCEPT_LANGUAGE'] = pattern[0]
            self.assertEquals(detect_language(req), pattern[1])

    def test_smart_truncate(self):
        """Test text truncation on word boundaries."""
        patterns = (
            ('text, teeext', 10, 'text,...'),
            ('somethingreallylongwithnospaces', 10, 'somethingr...'),
            ('short enough', 12, 'short enough'),
        )
        for pattern in patterns:
            eq_(smart_truncate(pattern[0], length=pattern[1]), pattern[2])


class ValidatorTests(TestCase):
    def test_url_in_text(self):
        """Find URLs in text."""
        patterns = (
            ('This contains no URLs.', False),
            ('I like the www. Do you?', False),
            ('If I write youtube.com, what happens?', False),
            ('Visit example.com/~myhomepage!', True),
            ('OMG http://foo.de', True),
            ('www.youtube.com is the best', True),
        )
        for pattern in patterns:
            if pattern[1]:
                self.assertRaises(ValidationError, validate_no_urls,
                                  pattern[0])
            else:
                validate_no_urls(pattern[0]) # Will fail if exception raised.

    def test_chrome_url(self):
        """Make sure URL validator allows chrome and about URLs."""
        v = ExtendedURLValidator()

        # These will fail if validation error is raised.
        v('about:blank')
        v('chrome://mozapps/content/downloads/downloads.xul')

        # These should fail.
        self.assertRaises(ValidationError, v, 'about:')
        self.assertRaises(ValidationError, v, 'chrome:bogus')


class VersionCompareTest(TestCase):
    def test_simplify_version(self):
        """Make sure version simplification works."""
        versions = {
            '4.0b1': '4.0b1',
            '3.6': '3.6',
            '3.6.4b1': '3.6.4b1',
            '3.6.4build1': '3.6.4',
            '3.6.4build17': '3.6.4',
        }
        for v in versions:
            self.assertEquals(simplify_version(v), versions[v])


class ViewTests(TestCase):

    fixtures = ['feedback/opinions']
    FX_UA = ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; '
             'de; rv:1.9.2.3) Gecko/20100401 Firefox/%s')

    def test_enforce_user_agent(self):
        """Make sure unknown user agents are forwarded to download page."""
        old_enforce_setting = settings.ENFORCE_USER_AGENT
        settings.ENFORCE_USER_AGENT = True

        # Let's detect the locale first
        self.client.get('/')

        # no UA: redirect
        r = self.client.get(reverse('feedback.sad'))
        self.assertEquals(r.status_code, 302)

        # old version: redirect
        r = self.client.get(reverse('feedback.sad'),
                            HTTP_USER_AGENT=self.FX_UA % '3.5')
        self.assertEquals(r.status_code, 302)
        self.assertTrue(r['Location'].endswith(reverse('feedback.need_beta')))

        # latest beta: no redirect
        r = self.client.get(
            reverse('feedback.sad'), HTTP_USER_AGENT=(self.FX_UA % (
                product_details.firefox_versions['LATEST_FIREFOX_DEVEL_VERSION'])))
        self.assertEquals(r.status_code, 200)

        # version newer than current: no redirect
        r = self.client.get(reverse('feedback.sad'),
                            HTTP_USER_AGENT=(self.FX_UA % '20.0'))
        self.assertEquals(r.status_code, 200)

        settings.ENFORCE_USER_AGENT = old_enforce_setting

    def test_give_feedback(self):
        r = self.client.post(reverse('feedback.sad'))
        eq_(r.content, 'User-Agent request header must be set.')

    def test_opinion_detail(self):
        r = self.client.get(reverse('opinion.detail', args=(29,)))
        eq_(r.status_code, 200)

    def test_url_submission(self):
        def submit_url(url, valid=True):
            """Submit feedback with a given URL, check if it's accepted."""
            r = self.client.post(
                reverse('feedback.sad'), {
                    # Need to vary text so we don't cause duplicates warnings.
                    'description': 'Hello %d' % datetime.now().microsecond,
                    'add_url': 'on',
                    'positive': 'True',
                    'url': url
                }, HTTP_USER_AGENT=(self.FX_UA % '20.0'), follow=True)
            # Neither valid nor invalid URLs cause anything but a 200 response.
            eq_(r.status_code, 200)
            if valid:
                assert r.content.find('Thanks') >= 0
                assert r.content.find('Enter a valid URL') == -1
            else:
                assert r.content.find('Thanks') == -1
                assert r.content.find('Enter a valid URL') >= 0

        # Valid URL types
        submit_url('http://example.com')
        submit_url('https://example.com')
        submit_url('about:me')
        submit_url('chrome://mozapps/content/extensions/extensions.xul')

        # Invalid URL types
        submit_url('gopher://something', valid=False)
        submit_url('zomg', valid=False)
