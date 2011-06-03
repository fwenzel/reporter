from datetime import datetime

from django.conf import settings

from nose.tools import eq_
from pyquery import PyQuery as pq

from input import OPINION_PRAISE, OPINION_ISSUE
from input.tests import ViewTestCase, enforce_ua
from input.urlresolvers import reverse
from feedback.models import Opinion


class BetaViewTests(ViewTestCase):
    """Tests for our beta feedback submissions."""

    fixtures = ['feedback/opinions']
    FX_UA = ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; '
             'de; rv:1.9.2.3) Gecko/20100401 Firefox/%s')

    def _get_page(self, ver=None):
        """Request beta feedback page."""
        extra = dict(HTTP_USER_AGENT=self.FX_UA % ver) if ver else {}
        return self.client.get(reverse('feedback'), **extra)

    @enforce_ua
    def test_no_ua(self):
        """No UA: Redirect to beta download."""
        r = self._get_page()
        eq_(r.status_code, 302)
        assert r['Location'].endswith(
                reverse('feedback.download'))

    @enforce_ua
    def test_release(self):
        r = self._get_page('4.0')
        eq_(r.status_code, 200)

    @enforce_ua
    def test_old_beta(self):
        """Old beta: redirect."""
        r = self._get_page('3.6b2')
        eq_(r.status_code, 302)
        assert r['Location'].endswith(reverse('feedback.download'))

    @enforce_ua
    def test_newer_beta(self):
        """Beta version newer than current: no redirect."""
        r = self._get_page('20.0b2')
        eq_(r.status_code, 200)

    @enforce_ua
    def test_nightly(self):
        """Nightly version: should be able to submit."""
        r = self._get_page('20.0a1')
        eq_(r.status_code, 200)
        r = self._get_page('20.0a2')
        eq_(r.status_code, 200)

    def test_give_feedback(self):
        r = self.client.post(reverse('feedback'))
        eq_(r.content, 'User-Agent request header must be set.')

    def test_opinion_detail(self):
        r = self.client.get(reverse('opinion.detail', args=(29,)))
        eq_(r.status_code, 200)

    def test_url_submission(self):
        def submit_url(url, valid=True):
            """Submit feedback with a given URL, check if it's accepted."""
            data = {
                # Need to vary text so we don't cause duplicates warnings.
                'description': 'Hello %d' % datetime.now().microsecond,
                'add_url': 'on',
                '_type': OPINION_PRAISE.id,
            }

            if url:
                data['url'] = url

            r = self.client.post(reverse('feedback'), data,
                                 HTTP_USER_AGENT=(self.FX_UA % '20.0b2'),
                                 follow=True)
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

        # Try submitting add_url=on with no URL. Bug 613549.
        submit_url(None)

    def test_submissions_without_url(self):
        """Ensure feedback without URL can be submitted. Bug 610023."""
        req = lambda: self.client.post(
            reverse('feedback'), {
                'description': 'Hello!',
                '_type': OPINION_ISSUE.id,
            }, HTTP_USER_AGENT=(self.FX_UA % '20.0b2'), follow=True)
        # No matter what you submit in the URL field, there must be a 200
        # response code.
        r = req()
        eq_(r.status_code, 200)
        assert r.content.find('Thanks for') >= 0

        # Resubmit, should not work due to duplicate submission.
        r2 = req()
        eq_(r2.status_code, 200)
        assert r2.content.find('We already got your feedback') >= 0

    def test_submission_autocomplete_off(self):
        """
        Ensure both mobile and desktop submission pages have autocomplete off.
        """
        def with_site(site_id):
            r = self.client.get(reverse('feedback'), HTTP_USER_AGENT=(
                self.FX_UA % '20.0b2'), SITE_ID=site_id, follow=True)
            d = pq(r.content)
            forms = d('article form')
            assert forms
            for form in forms:
                eq_(pq(form).attr('autocomplete'), 'off')

        with_site(settings.DESKTOP_SITE_ID)        
        with_site(settings.MOBILE_SITE_ID)


    def test_submission_with_device_info(self):
        """Ensure mobile device info can be submitted."""
        r = self.client.post(
            reverse('feedback'), {
                'description': 'Hello!',
                '_type': OPINION_ISSUE.id,
                'manufacturer': 'FancyBrand',
                'device': 'FancyPhone 2.0',
            }, HTTP_USER_AGENT=(self.FX_UA % '20.0b2'), follow=True)
        eq_(r.status_code, 200)
        assert r.content.find('Thanks') >= 0

        # Fetch row from model and check data made it there.
        latest = Opinion.objects.no_cache().order_by('-id')[0]
        eq_(latest.manufacturer, 'FancyBrand')
        eq_(latest.device, 'FancyPhone 2.0')

    def test_feedback_index(self):
        """Test feedback index page for Betas."""
        r = self.client.get(reverse('feedback'),
                            HTTP_USER_AGENT=(self.FX_UA % '20.0b2'),
                            follow=True)
        eq_(r.status_code, 200)
