from django.conf import settings

from mock import Mock, patch
from test_utils import eq_

from input import CHANNELS, urlresolvers
from input.tests import InputTestCase
from input.urlresolvers import reverse


class MiddlewareTests(InputTestCase):
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

    def test_redirect_with_querystring(self):
        r = self.client.get('/?foo=bar')
        eq_(r['Location'], 'http://testserver/en-US/release/?foo=bar')

    def test_redirect_with_locale(self):
        r = self.client.get(reverse('dashboard', channel='beta') + '?lang=fr')
        eq_(r['Location'], 'http://testserver/fr/beta/')

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

    def test_locale_in_get(self):
        request = Mock()
        request.path_info = '/'
        request.GET = dict(lang='en-US')
        p = urlresolvers.Prefixer(request)
        eq_(p.get_language(), 'en-US')
