# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
from functools import wraps

from django.conf import settings
from django.http import HttpRequest
from django.test.client import Client

import jingo
from mock import patch, Mock
from nose.tools import eq_
import test_utils

from input import urlresolvers, CHANNELS
from input.urlresolvers import reverse
from input.helpers import babel_date, timesince, urlparams


def enforce_ua(f):
    """Decorator to switch on UA enforcement for the duration of a test."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        old_enforce_setting = settings.ENFORCE_USER_AGENT
        try:
            settings.ENFORCE_USER_AGENT = True
            f(*args, **kwargs)
        finally:
            settings.ENFORCE_USER_AGENT = old_enforce_setting
    return wrapped


def render(s, context={}):
    """Render a Jinja2 template fragment."""
    t = jingo.env.from_string(s)
    return t.render(**context)


FX_UA = ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; '
         'en-US; rv:1.9.2.3) Gecko/20100401 Firefox/%s')


class TestCase(test_utils.TestCase):

    def setUp(self):
        super(TestCase, self).setUp()
        self.fxclient = Client(False, HTTP_USER_AGENT=(FX_UA % '4.0'))
        self.factory = test_utils.RequestFactory()


class ViewTestCase(test_utils.TestCase):
    def setUp(self):
        """Set up URL prefixer."""
        urlresolvers.set_url_prefix(urlresolvers.Prefixer(HttpRequest()))


class DecoratorTests(ViewTestCase):
    """Tests for our Input-wide view decorators."""

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
            reverse('feedback.suggestion'),
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


class HelperTests(test_utils.TestCase):
    def test_urlparams_unicode(self):
        """Make sure urlparams handles unicode well."""

        # Evil unicode
        url = u'/xx?evil=reco\ufffd\ufffd\ufffd\u02f5'
        urlparams(url)  # No error, please

        # Russian string (bug 580629)
        res = urlparams(u'/xx?russian=быстро')
        self.assertEqual(
            res, u'/xx?russian=%D0%B1%D1%8B%D1%81%D1%82%D1%80%D0%BE')

        # Polish string (bug 582506)
        res = urlparams(u'/xx?y=obsłudze')
        self.assertEqual(res, u'/xx?y=obs%C5%82udze')

    def test_absolute_url(self):
        """Build an absolute URL from a relative one."""
        request = HttpRequest()
        request.META = {'HTTP_HOST': 'example.com'}
        r = render('{{ absolute_url("/somewhere") }}', {'request': request})
        eq_(r, 'http://example.com/somewhere')

    def test_timesince(self):
        """Test timesince filter for common time deltas."""
        def ts(delta, expected):
            """Test timesince string for the given delta."""
            test_time = datetime.now() - timedelta(**delta)
            eq_(timesince(test_time), expected)

        ts(dict(seconds=55), 'just now')
        ts(dict(seconds=61), '1 minute ago')
        ts(dict(minutes=12), '12 minutes ago')
        ts(dict(minutes=65), '1 hour ago')
        ts(dict(hours=23), '23 hours ago')
        ts(dict(hours=47, minutes=59), '1 day ago')
        ts(dict(days=7), '7 days ago')
        ts(dict(days=8), babel_date(datetime.now() - timedelta(days=8)))

    def test_channel_switch(self):
        """Ensure URL reversal allows us to switch channels."""
        for ch in CHANNELS:
            eq_(render("{{ url('dashboard', channel='%s') }}" % ch),
                '/en-US/%s/' % ch)


class MiddlewareTests(TestCase):
    def test_locale_fallback(self):
        """
        Any specific flavor of a language (xx-YY) should return its generic
        site (xx) if it exists.
        """
        patterns = (
            ('en-us,en;q=0.7,de;q=0.8', 'en-US'),
            ('fr-FR,de-DE;q=0.5', 'fr'),
            ('zh, en-us;q=0.8, en;q=0.6', 'zh-CN'),
            ('xx-YY,es-ES;q=0.7,de-DE;q=0.5', 'es'),
            ('German', 'en-US'),  # invalid
            # bug 582075
            ('nb,no;q=0.8,nn;q=0.6,en-us;q=0.4,en;q=0.2', 'nb-NO'),
            # bug 629115
            ('en-US,en;q=0.9,ro;q=0.8,ja;q=0.7,fr;q=0.6', 'en-US'),
        )

        for pattern in patterns:
            r = self.client.get('/', HTTP_ACCEPT_LANGUAGE=pattern[0])
            eq_(r.status_code, 301)
            did_it_work = r['Location'].rstrip('/').endswith(
                    pattern[1] + '/' + settings.DEFAULT_CHANNEL)
            self.assertTrue(did_it_work, "%s didn't match %s" % pattern)

    def test_mobilesite_nohost(self):
        """Make sure we serve the desktop site if there's no HTTP_HOST set."""
        # This won't contain HTTP_HOST. Must not fail.
        self.client.get('/')
        eq_(settings.SITE_ID, settings.DESKTOP_SITE_ID)

    @patch('django.contrib.sites.models.Site.objects.get')
    def test_mobilesite_detection(self, mock):
        """Make sure we switch to the mobile site if the domain matches."""
        def side_effect(*args, **kwargs):
            class FakeSite(object):
                id = settings.MOBILE_SITE_ID
            return FakeSite()
        mock.side_effect = side_effect

        # Get the front page. Since we mocked the Site model, the URL we
        # pass here does not matter.
        self.client.get('/', HTTP_HOST='m.example.com')
        eq_(settings.SITE_ID, settings.MOBILE_SITE_ID)

    def test_x_frame_options(self):
        """Ensure X-Frame-Options middleware works as expected."""
        r = self.client.get('/')
        eq_(r['x-frame-options'], 'DENY')

    def test_no_prefixer(self):
        urlresolvers.clean_url_prefixes()
        eq_(urlresolvers.reverse('feedback.sad'), '/sad')

    def test_no_locale(self):
        request = Mock()
        request.path_info = '/beta'
        p = urlresolvers.Prefixer(request)
        eq_(p.channel, 'beta')

    def test_almost_locale(self):
        request = Mock()
        request.path_info = '/en/'
        p = urlresolvers.Prefixer(request)
        eq_(p.locale, 'en-US')

    def test_almost_locale_with_channel(self):
        request = Mock()
        request.path_info = '/en/release'
        p = urlresolvers.Prefixer(request)
        eq_(p.locale, 'en-US')
        eq_(p.channel, 'release')

    def test_fake_locale(self):
        r = self.factory.get('/zf/beta')
        p = urlresolvers.Prefixer(r)
        eq_(p.locale, '')
        eq_(p.channel, 'beta')

    def test_locale_in_get(self):
        request = Mock()
        request.path_info = '/'
        request.GET = dict(lang='en-US')
        p = urlresolvers.Prefixer(request)
        eq_(p.get_language(), 'en-US')

    def test_channel_in_get(self):
        for ch in CHANNELS:
            request = Mock()
            request.path_info = '/'
            request.GET = dict(channel=ch)
            p = urlresolvers.Prefixer(request)
            eq_(p.get_channel(), ch)

        # Invalid channel
        request = Mock()
        request.path_info = '/'
        request.GET = dict(channel='bogus')
        p = urlresolvers.Prefixer(request)
        eq_(p.get_channel(), settings.DEFAULT_CHANNEL)


class RedirectTests(TestCase):
    @enforce_ua
    def test_redirects(self):
        redirect = lambda x: '/en-US/%s/%s' % (settings.DEFAULT_CHANNEL, x)
        redirs = {
                '/feedback': '/en-US/release/feedback',
                '/thanks': '/en-US/%s/thanks' % settings.DEFAULT_CHANNEL,
                '/themes': '/en-US/%s/themes' % settings.DEFAULT_CHANNEL,
                '/sites': redirect('sites')
                }
        for link, redir in redirs.iteritems():
            self.assertRedirects(self.fxclient.get(link, follow=True), redir,
                                 301)

    def test_search(self):
        r = self.fxclient.get('/search', follow=True)
        assert r.status_code != 404
