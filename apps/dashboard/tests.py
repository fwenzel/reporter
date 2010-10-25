from nose.tools import eq_

from input.urlresolvers import reverse
from search.tests import SphinxTestCase


class TestDashboard(SphinxTestCase):
    def test_dashboard(self):
        r = self.client.get(reverse('dashboard'), follow=True)
        eq_(r.status_code, 200)
