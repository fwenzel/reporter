from django.test import TestCase
from django.conf import settings
from django.core.exceptions import ValidationError
from input.urlresolvers import reverse

from product_details import firefox_versions

from . import FIREFOX, MOBILE
from .utils import ua_parse
from .validators import validate_no_urls
from .version_compare import simplify_version


class UtilTests(TestCase):
    def test_ua_parse(self):
        """Test user agent parser for Firefox."""
        patterns = (
            # valid Fx
            ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; de; rv:1.9.2.3) '
             'Gecko/20100401 Firefox/3.6.3',
             FIREFOX, '3.6.3', 'de', 'mac'),
            ('Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.4) '
             'Gecko/20100611 Firefox/3.6.4 (.NET CLR 3.5.30729)',
             FIREFOX, '3.6.4', 'en-US', 'winxp'),
            # additional parentheses (bug 578339)
            ('Mozilla/5.0 (X11; U; Linux i686 (x86_64); en-US; rv:2.0b1) '
             'Gecko/20100628 Firefox/4.0b1',
             FIREFOX, '4.0b1', 'en-US', 'linux'),
            # locale fallback (bug 578339)
            ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; fr-FR; rv:2.0b1) '
             'Gecko/20100628 Firefox/4.0b1',
             FIREFOX, '4.0b1', 'fr', 'mac'),
            ('Mozilla/5.0 (X11; U; Linux x86_64; cs-CZ; rv:2.0b2pre) Gecko/20100630 '
             'Minefield/4.0b2pre',
             FIREFOX, '4.0b2pre', 'cs', 'linux'),

            # valid Fennec
            ('Mozilla/5.0 (X11; U; Linux armv6l; fr; rv:1.9.1b1pre) Gecko/'
             '20081005220218 Gecko/2008052201 Fennec/0.9pre',
             MOBILE, '0.9pre', 'fr', 'linux'),
            ('Mozilla/5.0 (X11; U; FreeBSD; en-US; rv:1.9.2a1pre) '
             'Gecko/20090626 Fennec/1.0b2',
             MOBILE, '1.0b2', 'en-US', 'other'),

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
                self.assertEquals(parsed['locale'], pattern[3])
                self.assertEquals(parsed['os'], pattern[4])
            else:
                self.assert_(parsed is None)


class ValidatorTests(TestCase):
    def test_url(self):
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
        FX_UA = ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; '
                 'de; rv:1.9.2.3) Gecko/20100401 Firefox/%s')
        r = self.client.get(reverse('feedback.sad'),
                            HTTP_USER_AGENT=FX_UA % '3.5')
        self.assertEquals(r.status_code, 302)
        self.assertTrue(r['Location'].endswith(reverse('feedback.need_beta')))

        # latest beta: no redirect
        r = self.client.get(reverse('feedback.sad'), HTTP_USER_AGENT=(
            FX_UA % firefox_versions['LATEST_FIREFOX_DEVEL_VERSION']))
        self.assertEquals(r.status_code, 200)

        # version newer than current: no redirect
        r = self.client.get(reverse('feedback.sad'),
                            HTTP_USER_AGENT=(FX_UA % '20.0'))
        self.assertEquals(r.status_code, 200)

        settings.ENFORCE_USER_AGENT = old_enforce_setting
