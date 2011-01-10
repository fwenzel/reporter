import copy
from datetime import datetime
import json

from django import http
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.exceptions import ValidationError
from django.test import TestCase

from nose.tools import eq_
from pyquery import pyquery

from input import RATING_USAGE, RATING_CHOICES
from input.tests import ViewTestCase
from input.urlresolvers import reverse
from feedback import (FIREFOX, MOBILE, OPINION_PRAISE, OPINION_ISSUE,
                      OPINION_SUGGESTION, OPINION_RATING, OPINION_BROKEN,
                      LATEST_BETAS, LATEST_RELEASE)
from feedback.models import Opinion
from feedback.utils import detect_language, ua_parse, smart_truncate
from feedback.validators import validate_no_urls, ExtendedURLValidator
from feedback.version_compare import (simplify_version, version_dict,
                                      version_int)


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

    def test_dict_vs_int(self):
        """
        version_dict and _int can use each other's data but must not overwrite
        it.
        """
        version_string = '4.0b8pre'
        dict1 = copy.copy(version_dict(version_string))
        int1 = version_int(version_string)
        dict2 = version_dict(version_string)
        int2 = version_int(version_string)
        eq_(dict1, dict2)
        eq_(int1, int2)


class BetaViewTests(ViewTestCase):
    """Tests for our beta feedback submissions."""

    fixtures = ['feedback/opinions']
    FX_UA = ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; '
             'de; rv:1.9.2.3) Gecko/20100401 Firefox/%s')

    def test_enforce_user_agent(self):
        """Make sure unknown user agents are forwarded to download page."""

        def get_page(ver=None):
            """Request beta feedback page."""
            extra = dict(HTTP_USER_AGENT=self.FX_UA % ver) if ver else {}
            return self.client.get(reverse('feedback.sad'),
                                   **extra)

        old_enforce_setting = settings.ENFORCE_USER_AGENT
        try:
            settings.ENFORCE_USER_AGENT = True

            # No UA: redirect.
            r = get_page()
            eq_(r.status_code, 302)

            # Release version: redirect.
            r = get_page('3.6')
            eq_(r.status_code, 302)
            assert r['Location'].endswith(reverse('feedback.release_feedback'))

            # Old beta: redirect.
            r = get_page('3.6b2')
            eq_(r.status_code, 302)
            assert r['Location'].endswith(reverse('feedback.need_beta'))

            # Latest beta: no redirect.
            r = get_page(LATEST_BETAS[FIREFOX])
            eq_(r.status_code, 200)

            # Beta version newer than current: no redirect.
            r = get_page('20.0b2')
            eq_(r.status_code, 200)

            # Nightly version: redirect.
            r = get_page('20.0b2pre')
            eq_(r.status_code, 302)
            assert r['Location'].endswith(reverse('feedback.need_beta'))

        finally:
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

    def test_enforce_user_agent(self):
        """Make sure unknown user agents are forwarded to download page."""

        def get_page(ver=None):
            """Request release feedback page."""
            extra = dict(HTTP_USER_AGENT=self.FX_UA % ver) if ver else {}
            return self.client.get(reverse('feedback.release_feedback'),
                                   **extra)

        old_enforce_setting = settings.ENFORCE_USER_AGENT
        try:
            settings.ENFORCE_USER_AGENT = True

            # No UA: redirect.
            r = get_page()
            eq_(r.status_code, 302)

            # Beta version: redirect.
            r = get_page('3.6b2')
            eq_(r.status_code, 302)
            assert r['Location'].endswith(reverse('feedback.beta_feedback'))

            # Old release: redirect.
            r = get_page('3.5')
            eq_(r.status_code, 302)
            assert r['Location'].endswith(reverse('feedback.need_release'))

            # Latest release: no redirect.
            r = get_page(LATEST_RELEASE[FIREFOX])
            eq_(r.status_code, 200)

            # Release version newer than current: no redirect.
            r = get_page('20.0')
            eq_(r.status_code, 200)

            # Nightly version: redirect.
            r = get_page('20.0b2pre')
            eq_(r.status_code, 302)
            print r['Location']
            assert r['Location'].endswith(reverse('feedback.need_release'))

        finally:
            settings.ENFORCE_USER_AGENT = old_enforce_setting

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
