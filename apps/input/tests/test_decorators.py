from django.conf import settings

from mock import patch
from test_utils import eq_

from input import decorators
from input.tests import ViewTestCase
from input.urlresolvers import reverse


class DecoratorTests(ViewTestCase):
    """Tests for our Input-wide decorators."""

    def test_cached_property(self):
        class A(object):
            _foo = 1

            @decorators.cached_property
            def foo(self):
                return self._foo

        a = A()
        eq_(a.foo, 1)
        a._foo = 2
        eq_(a.foo, 1)

    @patch('django.contrib.sites.models.Site.objects.get')
    def test_forward_mobile(self, mock):
        fake_mobile_domain = 'mymobiledomain.example.com'

        def side_effect(*args, **kwargs):
            class FakeSite(object):
                id = settings.MOBILE_SITE_ID
                domain = fake_mobile_domain
            return FakeSite()
        mock.side_effect = side_effect

        r = self.mclient.get(reverse('dashboard', channel='beta') + '?foo=bar')
        eq_(r.status_code, 301)
        eq_(r['Location'], 'http://' + fake_mobile_domain +
            reverse('dashboard', channel='beta') + '?foo=bar')

    @patch('django.contrib.sites.models.Site.objects.get')
    def test_mobile_device_detection(self, mock):
        """
        Requests to front page and submission pages should forward mobile
        users to mobile site.
        """
        fake_mobile_domain = 'mymobiledomain.example.com'

        def side_effect(*args, **kwargs):
            class FakeSite(object):
                id = settings.MOBILE_SITE_ID
                domain = fake_mobile_domain
            return FakeSite()
        mock.side_effect = side_effect

        # URLs that should allow Mobile detection
        urls = (
            reverse('dashboard', channel='beta'),
            reverse('feedback.happy'),
            reverse('feedback.sad'),
            reverse('feedback.idea'),
            reverse('feedback'),
        )

        # User Agent Patterns: (UA, forward: true/false?)
        ua_patterns = (
            # Fx
            ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; '
             'rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13', False),
            # MSIE
            ('Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)',
             False),
            # Fennec
            ('Mozilla/5.0 (X11; U; Linux armv6l; fr; rv:1.9.1b1pre) Gecko/'
             '20081005220218 Gecko/2008052201 Fennec/0.9pre', True),
            # iPod touch
            ('Mozilla/5.0 (iPod; U; CPU like Mac OS X; en) AppleWebKit/420.1 '
             '(KHTML, like Gecko) Version/3.0 Mobile/3A101a Safari/419.3',
             True),
        )
        for test_url in urls:
            for ua, forward_this in ua_patterns:
                r = self.client.get(test_url, HTTP_USER_AGENT=ua)
                if forward_this:
                    eq_(r.status_code, 301)
                    assert r['Location'].find(fake_mobile_domain) >= 0
                else:
                    assert (r.status_code == 200 or  # Page is served, or:
                            r.status_code / 100 == 3 and  # some redirect...
                            # ... but not to the mobile domain.
                            r['Location'].find(fake_mobile_domain) == -1)
