from django.conf import settings

import jingo
import jinja2
import test_utils
from jingo import register
from mock import Mock
from nose.tools import eq_
from pyquery import PyQuery as pq

import input
from dashboard import helpers
from input.tests import InputTestCase
from input.urlresolvers import reverse
from search.tests import SphinxTestCase


def render(s, context={}):
    t = jingo.env.from_string(s)
    return t.render(**context)


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

    def test_beta_dashboard(self):
        r = self.client.get(reverse('dashboard', channel='beta'))
        eq_(r.status_code, 200)

    def test_beta_pagination_link(self):
        r = self.client.get(reverse('dashboard', channel='beta'))
        doc = pq(r.content)

        pag_link = doc('.pager a.next')
        eq_(len(pag_link), 1)
        assert pag_link.attr('href').endswith(
            '?product=firefox&version=%s' % (
                input.LATEST_BETAS[input.FIREFOX]))


class TestMobileDashboard(test_utils.TestCase):
    def test_dashboard(self):
        r = self.client.get(reverse('dashboard', channel='beta'), follow=True,
                            SITE_ID=settings.MOBILE_SITE_ID)
        eq_(r.status_code, 200)


class TestHelpers(InputTestCase):
    def test_platform_none(self):
        """Test that PLATFORM with no name does not crash platform helper."""

        class TestPLATFORM(object):
            """Test PLATFORM with no name."""
            platform = None
            count = 10

        ctx = {
            'defaults': {'platform': None},
            'platforms': (TestPLATFORM(),),
            'opinion_count': 20
        }

        # No error, please.
        tpl = render_template('dashboard/mobile/platforms.html', ctx)
        assert tpl.find('id="platform_None"') >= 0

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

    def test_manufacturer_block(self):
        item = Mock()
        item.count = 50
        item.manufacturer = "RySny"
        ms = [item]
        r = render('{{ manufacturer_block(ms, 100) }}', dict(ms=ms))
        doc = pq(r)
        eq_(doc('input').attr('id'), 'brand_RySny')

    def test_device_block(self):
        item = Mock()
        item.count = 50
        item.device = "TacoTruck"
        ms = [item]
        r = render('{{ device_block(ms, 100) }}', dict(ms=ms))
        doc = pq(r)
        eq_(doc('input').attr('id'), 'device_TacoTruck')

    def test_sites_block(self):
        site = Mock()
        site.url = 'http://youtube.com'
        ms = [site]
        req = self.factory.get('/')
        req.mobile_site = False
        r = render('{{ sites_block(ms, 100) }}', dict(ms=ms, request=req))
        doc = pq(r)
        eq_(doc('strong').text(), 'youtube.com')

    def test_sites_block_mobile(self):
        site = Mock()
        site.url = 'http://youtube.com'
        site.size = 5
        ms = [site]
        req = self.factory.get('/')
        req.mobile_site = True
        req.default_prod = input.FIREFOX
        r = render('{{ sites_block(ms) }}', dict(ms=ms, request=req))
        doc = pq(r)
        eq_(doc('.label').text(), 'youtube.com')

    def test_mobile_bar(self):
        r = render('{{ mobile_bar("candy", "bar") }}')
        doc = pq(r)
        eq_(doc('label').text(), 'bar 100%')
        eq_(doc('label').attr('for'), 'candy')

    def test_versions_block(self):
        versions = [
            ('--', '-- all --'),
            ('3.0', '3.0'),
            ('3.6', '3.6'),
        ]
        version = '3.0'

        r = render('{{ versions_block(vs, v) }}', dict(vs=versions, v=version))
        doc = pq(r)

        eq_(doc('span.text').text(), version)
        eq_(len(doc('option')), len(versions))

        # Chosen version must have selected attribute
        sel = doc('option[selected]')
        eq_(len(sel), 1)
        eq_(sel.val(), version)
