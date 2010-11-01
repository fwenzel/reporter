from nose.tools import eq_

import test_utils

from input.urlresolvers import reverse
from search.tests import SphinxTestCase


class TestDashboard(SphinxTestCase):
    def test_dashboard(self):
        r = self.client.get(reverse('dashboard'), follow=True)
        eq_(r.status_code, 200)

class TestMobileDashboard(test_utils.TestCase):
    def setUp(self):
        from django.conf import settings
        settings.SITE_ID = 2

    def test_dashboard(self):
        r = self.client.get(reverse('dashboard'), follow=True)
        eq_(r.status_code, 200)
