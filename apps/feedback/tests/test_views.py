from datetime import datetime
import json

from django.conf import settings

from nose.tools import eq_
from pyquery import pyquery

from input import (FIREFOX, LATEST_BETAS, LATEST_RELEASE, OPINION_PRAISE,
                   OPINION_ISSUE, OPINION_SUGGESTION, OPINION_RATING,
                   OPINION_BROKEN, RATING_USAGE, RATING_CHOICES,
		   MAX_FEEDBACK_LENGTH, MAX_SUGGESTION_LENGTH )
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
        return self.client.get(reverse('feedback.sad'), **extra)

    @enforce_ua
    def test_no_ua(self):
        """No UA: Redirect to beta download."""
        r = self._get_page()
        eq_(r.status_code, 302)
        assert r['Location'].endswith(
                reverse('feedback.download', channel='beta'))

    @enforce_ua
    def test_release(self):
        """Release version on beta page: redirect."""
        r = self._get_page('3.6')
        eq_(r.status_code, 302)
        assert r['Location'].endswith(reverse('feedback', channel='release'))

    @enforce_ua
    def test_old_beta(self):
        """Old beta: redirect."""
        r = self._get_page('3.6b2')
        eq_(r.status_code, 302)
        assert r['Location'].endswith(
                reverse('feedback.download', channel='beta'))

    @enforce_ua
    def test_latest_beta(self):
        """Latest beta: no redirect."""
        r = self._get_page(LATEST_BETAS[FIREFOX])
        eq_(r.status_code, 200)

    @enforce_ua
    def test_newer_beta(self):
        """Beta version newer than current: no redirect."""
        r = self._get_page('20.0b2')
        eq_(r.status_code, 200)

    @enforce_ua
    def test_nightly(self):
        """Nightly version: redirect."""
        r = self._get_page('20.0b2pre')
        eq_(r.status_code, 302)
        assert r['Location'].endswith(
                reverse('feedback.download', channel='beta'))

    def test_give_feedback(self):
        r = self.client.post(reverse('feedback.sad'))
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
                'type': OPINION_PRAISE.id,
            }

            if url:
                data['url'] = url

            r = self.client.post(reverse('feedback.happy'), data,
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
            reverse('feedback.sad'), {
                'description': 'Hello!',
                'type': OPINION_ISSUE.id,
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
        def autocomplete_check(site_id):
            r = self.client.get(reverse('feedback.sad'), HTTP_USER_AGENT=(
                self.FX_UA % '20.0b2'), SITE_ID=site_id, follow=True)
            doc = pyquery.PyQuery(r.content)
            form = doc('#feedbackform form')

            assert form
            eq_(form.attr('autocomplete'), 'off')

        autocomplete_check(settings.DESKTOP_SITE_ID)
        autocomplete_check(settings.MOBILE_SITE_ID)

    def test_submission_with_device_info(self):
        """Ensure mobile device info can be submitted."""
        r = self.client.post(
            reverse('feedback.sad'), {
                'description': 'Hello!',
                'type': OPINION_ISSUE.id,
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
        r = self.client.get(reverse('feedback', channel='beta'),
                            HTTP_USER_AGENT=(self.FX_UA % '20.0b2'),
                            follow=True)
        eq_(r.status_code, 200)
        doc = pyquery.PyQuery(r.content)
        for link in ('feedback.happy', 'feedback.sad'):
            eq_(doc('a[href$="%s"]' % reverse(link)).length, 1)

    def test_max_length(self):
        """
        Ensure description's max_length attribute is propagated correctly for
        JS to pick up.
        """
        for link in ('feedback.happy', 'feedback.sad'):
            r = self.client.get(reverse(link, channel='beta'),
                                HTTP_USER_AGENT=(self.FX_UA % '20.0b2'),
                                follow=True)
            doc = pyquery.PyQuery(r.content)
            eq_(doc('#count').attr('data-max'),
                str(MAX_FEEDBACK_LENGTH))


class ReleaseTests(ViewTestCase):
    """Test feedback for Firefox release versions."""

    FX_UA = ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; '
             'de; rv:1.9.2.3) Gecko/20100401 Firefox/%s')

    def _get_page(self, ver=None):
        """Request release feedback page."""
        extra = dict(HTTP_USER_AGENT=self.FX_UA % ver) if ver else {}

        return self.client.get(reverse('feedback', channel='release'), **extra)

    @enforce_ua
    def test_no_ua(self):
        """No UA: redirect."""
        r = self._get_page()
        eq_(r.status_code, 302)
        assert r['Location'].endswith(reverse('feedback.download',
                                              channel='release'))

    @enforce_ua
    def test_beta(self):
        """Beta version on release page: redirect."""
        r = self._get_page('3.6b2')
        self.assertRedirects(r, reverse('feedback', channel='beta'), 302, 302)

    @enforce_ua
    def test_old_release(self):
        """Old release: redirect."""
        r = self._get_page('3.5')
        eq_(r.status_code, 302)
        assert r['Location'].endswith(reverse('feedback.download',
                                              channel='release'))

    @enforce_ua
    def test_latest_release(self):
        """Latest release: no redirect."""
        r = self._get_page(LATEST_RELEASE[FIREFOX])
        eq_(r.status_code, 200)

    @enforce_ua
    def test_newer_release(self):
        """Release version newer than current: no redirect."""
        r = self._get_page('20.0')
        eq_(r.status_code, 200)

    @enforce_ua
    def test_nightly(self):
        """Nightly version: redirect."""
        r = self._get_page('20.0b2pre')
        eq_(r.status_code, 302)
        assert r['Location'].endswith(reverse('feedback.download',
                                              channel='beta'))

    def post_feedback(self, data, ajax=False, follow=True):
        """POST to the release feedback page."""
        options = dict(HTTP_USER_AGENT=(self.FX_UA % '20.0'), follow=follow)
        if ajax:
            options['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'

        return self.client.post(reverse('feedback', channel='release'), data,
                                **options)

    def test_feedback_loads(self):
        """No general errors on release feedback page."""
        r = self.client.get(reverse('feedback', channel='release'),
                            HTTP_USER_AGENT=(self.FX_UA % '20.0'),
                            follow=True)
        eq_(r.status_code, 200)
        doc = pyquery.PyQuery(r.content)
        # Find all three forms
        eq_(doc('article form').length, 3)

    def test_feedback_wrongtype(self):
        """Test that giving a wrong type generates a 400."""
        r = self.post_feedback(dict(type=99, follow=False, ajax=True))
        eq_(r.status_code, 400)

    def test_rating(self):
        """Submit rating form with and without AJAX."""
        data = {'type': OPINION_RATING.id}
        for type in RATING_USAGE:
            data[type.short] = RATING_CHOICES[type.id % len(RATING_CHOICES)][0]

        for ajax in True, False:
            r = self.post_feedback(data, follow=False, ajax=ajax)
            if not ajax:
                eq_(r.status_code, 302)
                assert r['Location'].endswith(
                        reverse('feedback', channel='release') + '#thanks')
            else:
                eq_(r.status_code, 200)
                eq_(r['Content-Type'], 'application/json')

            # Check the content made it into the database.
            latest = Opinion.objects.no_cache().order_by('-id')[0]
            eq_(latest.ratings.count(), len(RATING_USAGE))
            latest.delete()

    def test_rating_errors(self):
        # Empty POST: Count errors
        for ajax in True, False:
            r = self.post_feedback({'type': OPINION_RATING.id}, ajax=ajax)
            if not ajax:
                doc = pyquery.PyQuery(r.content)
                eq_(doc('article#rate form .errorlist').text(),
                    'Please rate at least one item.')
            else:
                eq_(r.status_code, 400)
                errors = json.loads(r.content)
                eq_(len(errors), 1)

    def test_rating_one_item(self):
        data = {'type': OPINION_RATING.id}
        type = RATING_USAGE[0]
        data[type.short] = 1
        r = self.post_feedback(data, ajax=True)
        eq_(r.status_code, 200)
        latest = Opinion.objects.no_cache().order_by('-id')[0]
        eq_(latest.ratings.count(), 1)

    def test_broken(self):
        """Submit broken website report with and without AJAX."""
        # Empty POST: Count errors
        for ajax in True, False:
            r = self.post_feedback({'type': OPINION_BROKEN.id}, ajax=ajax)
            if not ajax:
                doc = pyquery.PyQuery(r.content)
                eq_(doc('article#broken form .errorlist').length, 2)
            else:
                eq_(r.status_code, 400)
                errors = json.loads(r.content)
                assert 'url' in errors
                assert 'description' in errors

        # Submit actual form
        data = {
            'type': OPINION_BROKEN.id,
            'url': 'http://example.com/broken',
            'description': 'This does not work.',
        }

        for ajax in True, False:
            r = self.post_feedback(data, follow=False, ajax=ajax)
            if not ajax:
                eq_(r.status_code, 302)
                assert r['Location'].endswith(
                        reverse('feedback', channel='release') + '#thanks')
            else:
                eq_(r.status_code, 200)
                eq_(r['Content-Type'], 'application/json')

            # Check the content made it into the database.
            latest = Opinion.objects.no_cache().order_by('-id')[0]
            eq_(latest.description, data['description'])
            eq_(latest.url, data['url'])
            latest.delete()

    def test_suggestion(self):
        """Submit suggestion with and without AJAX."""
        # Empty POST: Count errors
        for ajax in True, False:
            r = self.post_feedback({'type': OPINION_SUGGESTION.id}, ajax=ajax)
            if not ajax:
                doc = pyquery.PyQuery(r.content)
                eq_(doc('article#idea form .errorlist').length, 1)
            else:
                eq_(r.status_code, 400)
                errors = json.loads(r.content)
                assert 'description' in errors

        # Submit actual form
        data = {
            'type': OPINION_SUGGESTION.id,
            'description': 'This is a suggestion.',
        }

        for ajax in True, False:
            r = self.post_feedback(data, follow=False, ajax=ajax)
            if not ajax:
                eq_(r.status_code, 302)
                assert r['Location'].endswith(
                        reverse('feedback', channel='release') + '#thanks')
            else:
                eq_(r.status_code, 200)
                eq_(r['Content-Type'], 'application/json')

            # Check the content made it into the database.
            latest = Opinion.objects.no_cache().order_by('-id')[0]
            eq_(latest.description, data['description'])
            latest.delete()

    def test_max_length(self):
        """
        Ensure description's max_length attribute is propagated correctly for
        JS to pick up.
        """
        r = self.client.get(reverse('feedback', channel='release'),
                            HTTP_USER_AGENT=(self.FX_UA % '20.0'),
                            follow=True)
        doc = pyquery.PyQuery(r.content)
        eq_(doc('#count-broken-desc').attr('data-max'),
            str(MAX_FEEDBACK_LENGTH))
        eq_(doc('#count-idea-desc').attr('data-max'),
            str(MAX_SUGGESTION_LENGTH))
