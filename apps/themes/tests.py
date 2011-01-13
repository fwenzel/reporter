from django.conf import settings

import test_utils
from nose.tools import eq_

from input.urlresolvers import reverse
from feedback import LATEST_BETAS, FIREFOX
from feedback.models import Opinion
from pyquery import PyQuery as pq

from themes.models import Theme


class TestViews(test_utils.TestCase):
    def setUp(self):
        self.client.get('/')
        settings.CLUSTER_SIM_THRESHOLD = 2

        args = dict(product=1, version=LATEST_BETAS[FIREFOX], os='mac',
                    locale='en-US')
        for x in xrange(10):
            o = Opinion(description='Skip town. slow down '
                        'Push it to the ' + x * 'east coast ',
                        **args)
            o.save()

        for x in xrange(10):
            o = Opinion(description='Despite all my rage, '
                        'I am still just a rat in a ' + x * 'cage ',
                        **args)
            o.save()

        for x in xrange(4):
            o = Opinion(description='It is hammer time ' + x * 'baby ',
                        **args)
            o.save()

        for x in xrange(2):
            o = Opinion(description='Three blind mice.', **args)
            o.save()

        o = Opinion(description='Hello World', **args)
        o.save()

        from themes.cron import cluster
        cluster()

    def test_theme_count(self):
        """Make sure the right number of themes has been generated."""
        eq_(Theme.objects.count(), 6)
        eq_(Theme.objects.filter(platform='').count(), 3)

    def test_index(self):
        r = self.client.get(reverse('themes'))
        eq_(r.status_code, 200)
        doc = pq(r.content)
        for theme in doc('.theme'):
            eq_(theme.attrib.get('data-platform'), 'aggregate')

    def test_filters(self):
        r = self.client.get(reverse('themes') + '?s=sad')
        eq_(r.status_code, 200)
        r = self.client.get(reverse('themes') + '?p=mac')
        eq_(r.status_code, 200)

    def test_invalid_filters(self):
        """Handle invalid params gracefully."""
        r = self.client.get(reverse('themes') + '?a=somethinginvalid')
        eq_(r.status_code, 404)

    def test_invalid_theme(self):
        """Try to get a theme using a nonexistent ID (bug 617439)."""
        id = Theme.objects.all()[0].id
        r = self.client.get(reverse('theme', kwargs={"theme_id": id + 99}))
        eq_(r.status_code, 404)
