from django.conf import settings

from jingo import register
import jinja2
from nose.tools import eq_
import test_utils

from input.urlresolvers import reverse
from search.tests import SphinxTestCase


def render_template(template, context):
    """Helper rendering a Jinja template."""
    t = register.env.get_template(template).render(context)
    return jinja2.Markup(t)


class TestDashboard(SphinxTestCase):
    def test_root(self):
        """Ensure our site root always works."""
        r = self.client.get('/', follow=True)
        eq_(r.status_code, 200)

    def test_dashboard(self):
        r = self.client.get(reverse('dashboard'), follow=True)
        eq_(r.status_code, 200)


class TestMobileDashboard(test_utils.TestCase):
    def test_dashboard(self):
        r = self.client.get(reverse('dashboard'), follow=True,
                            SITE_ID=settings.MOBILE_SITE_ID)
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

    def test_locale_none(self):
        """Test that locale with no name does not crash locale helper."""

        class TestLocale(object):
            """Test locale with no name."""
            locale = None
            count = 10

        ctx = {
            'defaults': {'locale': None},
            'locales': (TestLocale(),),
            'opinion_count': 20
        }

        # No error, please.
        tpl = render_template('dashboard/mobile/locales.html', ctx)
        assert tpl.find('id="loc_None"') >= 0
