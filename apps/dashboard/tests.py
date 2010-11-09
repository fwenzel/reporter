from nose.tools import eq_

from jingo import register
import jinja2
import test_utils

from input.urlresolvers import reverse
from search.tests import SphinxTestCase


def render_template(template, context):
    """Helper rendering a Jinja template."""
    t = register.env.get_template(template).render(context)
    return jinja2.Markup(t)


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


class TestHelpers(test_utils.TestCase):
    def test_os_none(self):
        """Test that OS with no name does not crash platform helper."""

        class TestOS(object):
            """Test OS with no name."""
            os = None
            count = 10

        ctx = {
            'defaults': {'os': None},
            'platforms': (TestOS(),),
            'opinion_count': 20
        }

        # No error, please.
        tpl = render_template('dashboard/mobile/platforms.html', ctx)
        assert tpl.find('id="os_None"') >= 0
