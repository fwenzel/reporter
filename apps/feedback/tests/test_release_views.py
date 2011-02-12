import json

from nose.tools import eq_
from pyquery import PyQuery as pq

from feedback.models import Opinion
from input import (
    FIREFOX, LATEST_RELEASE, MAX_FEEDBACK_LENGTH, MAX_IDEA_LENGTH,
    OPINION_BROKEN, OPINION_IDEA, OPINION_RATING,
    RATING_CHOICES, RATING_USAGE)
from input.tests import FX_UA, ViewTestCase, enforce_ua
from input.urlresolvers import reverse


class ReleaseTests(ViewTestCase):
    """Test feedback for Firefox release versions."""

    def _get_page(self, ver=None):
        """Request release feedback page."""
        extra = dict(HTTP_USER_AGENT=FX_UA % ver) if ver else {}

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
        options = dict(HTTP_USER_AGENT=(FX_UA % '20.0'), follow=follow)
        if ajax:
            options['HTTP_X_REQUESTED_WITH'] = 'XMLHttpRequest'

        return self.client.post(reverse('feedback', channel='release'), data,
                                **options)

    def test_feedback_loads(self):
        """No general errors on release feedback page."""
        r = self.client.get(reverse('feedback', channel='release'),
                            HTTP_USER_AGENT=(FX_UA % '20.0'),
                            follow=True)
        eq_(r.status_code, 200)
        doc = pq(r.content)
        # Find all three forms
        eq_(doc('article form').length, 3)

    def test_feedback_wrongtype(self):
        """Test that giving a wrong type generates a 400."""
        # Wrong number
        r = self.post_feedback(dict(type=99, follow=False, ajax=True))
        eq_(r.status_code, 400)

        # Not a number
        r = self.post_feedback(dict(type='pancakes', follow=False, ajax=True))
        eq_(r.status_code, 400)

        # No type
        r = self.post_feedback(dict(follow=False, ajax=True))
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
                doc = pq(r.content)
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
                doc = pq(r.content)
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

    def test_idea(self):
        """Submit idea with and without AJAX."""
        # Empty POST: Count errors
        for ajax in True, False:
            r = self.post_feedback({'type': OPINION_IDEA.id}, ajax=ajax)
            if not ajax:
                doc = pq(r.content)
                eq_(doc('article#idea form .errorlist').length, 1)
            else:
                eq_(r.status_code, 400)
                errors = json.loads(r.content)
                assert 'description' in errors

        # Submit actual form
        data = {
            'type': OPINION_IDEA.id,
            'description': 'This is an idea.',
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
                            HTTP_USER_AGENT=(FX_UA % '20.0'),
                            follow=True)
        doc = pq(r.content)
        eq_(doc('#count-broken-desc').attr('data-max'),
            str(MAX_FEEDBACK_LENGTH))
        eq_(doc('#count-idea-desc').attr('data-max'),
            str(MAX_IDEA_LENGTH))
