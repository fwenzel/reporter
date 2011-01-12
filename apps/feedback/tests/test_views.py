from datetime import datetime
from functools import wraps
import json

from django.conf import settings

from nose.tools import eq_
from pyquery import pyquery

from input import RATING_USAGE, RATING_CHOICES
from input.tests import ViewTestCase
from input.urlresolvers import reverse
from feedback import (FIREFOX, OPINION_PRAISE, OPINION_ISSUE,
                      OPINION_SUGGESTION, OPINION_RATING, OPINION_BROKEN,
                      LATEST_BETAS, LATEST_RELEASE)
from feedback.models import Opinion


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


class BetaViewTests(ViewTestCase):
    """Tests for our beta feedback submissions."""

    fixtures = ['feedback/opinions']
    FX_UA = ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; '
             'de; rv:1.9.2.3) Gecko/20100401 Firefox/%s')

    def _get_page(self, ver=None):
        """Request beta feedback page."""
        extra = dict(HTTP_USER_AGENT=self.FX_UA % ver) if ver else {}
        return self.client.get(reverse('feedback.sad'),
                               **extra)

    @enforce_ua
    def test_no_ua(self):
        """No UA: Redirect to beta download."""
        r = self._get_page()
        eq_(r.status_code, 302)
        assert r['Location'].endswith(reverse('feedback.need_beta'))

    @enforce_ua
    def test_release(self):
        """Release version on beta page: redirect."""
        r = self._get_page('3.6')
        eq_(r.status_code, 302)
        assert r['Location'].endswith(reverse('feedback.release_feedback'))

    @enforce_ua
    def test_old_beta(self):
        """Old beta: redirect."""
        r = self._get_page('3.6b2')
        eq_(r.status_code, 302)
        assert r['Location'].endswith(reverse('feedback.need_beta'))

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
        assert r['Location'].endswith(reverse('feedback.need_beta'))

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
                'type': OPINION_PRAISE,
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
        r = self.client.post(
            reverse('feedback.sad'), {
                'description': 'Hello!',
                'type': OPINION_ISSUE,
            }, HTTP_USER_AGENT=(self.FX_UA % '20.0b2'), follow=True)
        # No matter what you submit in the URL field, there must be a 200
        # response code.
        eq_(r.status_code, 200)
        assert r.content.find('Thanks') >= 0

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
            print r

        autocomplete_check(settings.DESKTOP_SITE_ID)
        autocomplete_check(settings.MOBILE_SITE_ID)

    def test_submission_with_device_info(self):
        """Ensure mobile device info can be submitted."""
        r = self.client.post(
            reverse('feedback.sad'), {
                'description': 'Hello!',
                'type': OPINION_ISSUE,
                'manufacturer': 'FancyBrand',
                'device': 'FancyPhone 2.0',
            }, HTTP_USER_AGENT=(self.FX_UA % '20.0b2'), follow=True)
        eq_(r.status_code, 200)
        assert r.content.find('Thanks') >= 0

        # Fetch row from model and check data made it there.
        latest = Opinion.objects.no_cache().order_by('-id')[0]
        eq_(latest.manufacturer, 'FancyBrand')
        eq_(latest.device, 'FancyPhone 2.0')


class ReleaseViewTests(ViewTestCase):
    """Test feedback for Firefox release versions."""

    FX_UA = ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; '
             'de; rv:1.9.2.3) Gecko/20100401 Firefox/%s')

    def _get_page(self, ver=None):
        """Request release feedback page."""
        extra = dict(HTTP_USER_AGENT=self.FX_UA % ver) if ver else {}
        return self.client.get(reverse('feedback.release_feedback'),
                               **extra)

    @enforce_ua
    def test_no_ua(self):
        """No UA: redirect."""
        r = self._get_page()
        eq_(r.status_code, 302)
        assert r['Location'].endswith(reverse('feedback.need_release'))

    @enforce_ua
    def test_beta(self):
        """Beta version on release page: redirect."""
        r = self._get_page('3.6b2')
        eq_(r.status_code, 302)
        assert r['Location'].endswith(reverse('feedback.beta_feedback'))

    @enforce_ua
    def test_old_release(self):
        """Old release: redirect."""
        r = self._get_page('3.5')
        eq_(r.status_code, 302)
        assert r['Location'].endswith(reverse('feedback.need_release'))

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
        assert r['Location'].endswith(reverse('feedback.need_beta'))

    def post_feedback(self, data, ajax=False, follow=True):
        """POST to the release feedback page."""
        options = dict(HTTP_USER_AGENT=(self.FX_UA % '20.0'), follow=follow)
        if ajax:
            options['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'

        return self.client.post(reverse('feedback.release_feedback'), data,
                                **options)

    def test_feedback_loads(self):
        """No general errors on release feedback page."""
        r = self.client.get(reverse('feedback.release_feedback'),
                            HTTP_USER_AGENT=(self.FX_UA % '20.0'),
                            follow=True)
        eq_(r.status_code, 200)
        doc = pyquery.PyQuery(r.content)
        # Find all three forms
        eq_(doc('article form').length, 3)

    def test_rating(self):
        """Submit rating form with and without AJAX."""

        # Empty POST: Count errors
        for ajax in True, False:
            r = self.post_feedback({'type': OPINION_RATING}, ajax=ajax)
            if not ajax:
                doc = pyquery.PyQuery(r.content)
                eq_(doc('article#rate form .errorlist').length, len(RATING_USAGE))
            else:
                eq_(r.status_code, 400)
                errors = json.loads(r.content)
                eq_(len(errors), len(RATING_USAGE))
                for question in RATING_USAGE:
                    assert question.short in errors

        # Submit actual rating
        data = {'type': OPINION_RATING}
        for type in RATING_USAGE:
            data[type.short] = RATING_CHOICES[type.id % len(RATING_CHOICES)][0]

        for ajax in True, False:
            r = self.post_feedback(data, follow=False, ajax=ajax)
            if not ajax:
                eq_(r.status_code, 302)
                assert r['Location'].endswith(
                    reverse('feedback.release_feedback') + '#thanks')
            else:
                eq_(r.status_code, 200)
                eq_(r['Content-Type'], 'application/json')

            # Check the content made it into the database.
            latest = Opinion.objects.no_cache().order_by('-id')[0]
            eq_(latest.ratings.count(), len(RATING_USAGE))
            latest.delete()

    def test_broken(self):
        """Submit broken website report with and without AJAX."""
        # Empty POST: Count errors
        for ajax in True, False:
            r = self.post_feedback({'type': OPINION_BROKEN}, ajax=ajax)
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
            'type': OPINION_BROKEN,
            'url': 'http://example.com/broken',
            'description': 'This does not work.',
        }

        for ajax in True, False:
            r = self.post_feedback(data, follow=False, ajax=ajax)
            if not ajax:
                eq_(r.status_code, 302)
                assert r['Location'].endswith(
                    reverse('feedback.release_feedback') + '#thanks')
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
            r = self.post_feedback({'type': OPINION_SUGGESTION}, ajax=ajax)
            if not ajax:
                doc = pyquery.PyQuery(r.content)
                eq_(doc('article#idea form .errorlist').length, 1)
            else:
                eq_(r.status_code, 400)
                errors = json.loads(r.content)
                assert 'description' in errors

        # Submit actual form
        data = {
            'type': OPINION_SUGGESTION,
            'description': 'This is a suggestion.',
        }

        for ajax in True, False:
            r = self.post_feedback(data, follow=False, ajax=ajax)
            if not ajax:
                eq_(r.status_code, 302)
                assert r['Location'].endswith(
                    reverse('feedback.release_feedback') + '#thanks')
            else:
                eq_(r.status_code, 200)
                eq_(r['Content-Type'], 'application/json')

            # Check the content made it into the database.
            latest = Opinion.objects.no_cache().order_by('-id')[0]
            eq_(latest.description, data['description'])
            latest.delete()

