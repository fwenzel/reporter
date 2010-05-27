from django.test import TestCase
from django.conf import settings
from django.core.urlresolvers import reverse

from product_details import firefox_versions

from . import FIREFOX, MOBILE
from .utils import ua_parse


class UtilTests(TestCase):
    def test_ua_parse(self):
        """Test user agent parser for Firefox."""
        patterns = [
            # valid Fx
            ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; de; rv:1.9.2.3) '
             'Gecko/20100401 Firefox/3.6.3',
             FIREFOX, '3.6.3', 'de', 'mac'),

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
        ]

        for pattern in patterns:
            parsed = ua_parse(pattern[0])
            if pattern[1]:
                assert parsed['browser'] == pattern[1]
                assert parsed['version'] == pattern[2]
                assert parsed['locale'] == pattern[3]
                assert parsed['os'] == pattern[4]
            else:
                assert parsed is None


class ViewTests(TestCase):
    def test_enforce_user_agent(self):
        """Make sure unknown user agents are forwarded to download page."""
        old_enforce_setting = settings.ENFORCE_USER_AGENT
        settings.ENFORCE_USER_AGENT = True

        # no UA: redirect
        r = self.client.get(reverse('feedback.sad'))
        self.assertEquals(r.status_code, 302)

        # old version: redirect
        FX_UA = ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; '
                 'de; rv:1.9.2.3) Gecko/20100401 Firefox/%s')
        r = self.client.get(reverse('feedback.sad'), {'ua': FX_UA % '3.6.3'})
        self.assertEquals(r.status_code, 302)
        self.assertEquals(r['Location'], settings.URL_BETA)

        # latest beta: no redirect
        r = self.client.get(reverse('feedback.sad'), {
            'ua': FX_UA % firefox_versions['LATEST_FIREFOX_DEVEL_VERSION']})
        self.assertEquals(r.status_code, 200)

        settings.ENFORCE_USER_AGENT = old_enforce_setting
