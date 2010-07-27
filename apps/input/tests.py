# -*- coding: utf-8 -*-
from django.conf import settings

from mock import patch
from nose.tools import eq_
import test_utils

from .helpers import urlparams


class HelperTests(test_utils.TestCase):
    def test_urlparams_unicode(self):
        """Make sure urlparams handles unicode well."""

        # Evil unicode
        url = u'/xx?evil=reco\ufffd\ufffd\ufffd\u02f5'
        urlparams(url) # No error, please

        # Russian string (bug 580629)
        res = urlparams(u'/xx?russian=быстро')
        self.assertEqual(
            res, u'/xx?russian=%D0%B1%D1%8B%D1%81%D1%82%D1%80%D0%BE')


class MiddlewareTests(test_utils.TestCase):
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
