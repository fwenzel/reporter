# -*- coding: utf-8 -*-
from datetime import datetime, timedelta

from django.http import HttpRequest

from mock import Mock, patch
from pyquery import PyQuery as pq
from test_utils import eq_

from input import CHANNELS, helpers
from input.helpers import babel_date, isotime, timesince, urlparams
from input.tests import InputTestCase, render


class HelperTests(InputTestCase):
    def test_absolute_url(self):
        """Build an absolute URL from a relative one."""
        request = HttpRequest()
        request.META = {'HTTP_HOST': 'example.com'}
        r = render('{{ absolute_url("/somewhere") }}', {'request': request})
        eq_(r, 'http://example.com/somewhere')

    def test_channel_switch(self):
        """Ensure URL reversal allows us to switch channels."""
        for ch in CHANNELS:
            eq_(render("{{ url('dashboard', channel='%s') }}" % ch),
                '/en-US/%s/' % ch)

    @patch('input.helpers.translation.get_language')
    def test_get_format(self, get_language):
        """Ensure unknown locale falls back to default locale in get_format."""
        get_language.return_value = 'fuuuuu'
        eq_(str(helpers._get_format().locale), 'en_US')

    def test_isotime_fake_time(self):
        eq_(helpers.isotime(None), None)

    def test_pager(self):
        page = Mock()
        page.has_previous.return_value = True
        page.has_next.return_value = True
        request = self.factory.get('/')
        t = render('{{ pager() }}', dict(request=request, page=page))
        doc = pq(t)
        assert doc('a.next')
        assert doc('a.prev')

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
