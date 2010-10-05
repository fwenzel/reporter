from django.conf import settings

import test_utils
from nose.tools import eq_

from input.urlresolvers import reverse
from feedback import LATEST_BETAS, FIREFOX
from feedback.models import Opinion


class TestViews(test_utils.TestCase):
    def setUp(self):
        self.client.get('/')
        settings.CLUSTER_SIM_THRESHOLD = 0.1

        args = dict(product=1, version=LATEST_BETAS[FIREFOX], os='mac',
                    locale='en-US')
        for x in xrange(10):
            o = Opinion(description='Skip town. slow down '
                        'Push it to the east coast ' + str(x),
                        **args)
            o.save()

        for x in xrange(10):
            o = Opinion(description='Despite all my rage, '
                        'I am still just a rat in a cage.' + str(x),
                        **args
                       )
            o.save()

        for x in xrange(4):
            o = Opinion(description='It is hammer time baby.  ' + str(x),
                        **args
                       )
            o.save()

        for x in xrange(2):
            o = Opinion(description='Three blind mice.', **args)
            o.save()

        o = Opinion(description='Hello World', **args)
        o.save()

        from themes.cron import cluster
        cluster()

    def test_index(self):
        r = self.client.get(reverse('themes'))
        eq_(r.status_code, 200)

    def test_filters(self):
        r = self.client.get(reverse('themes') + '?s=sad')
        eq_(r.status_code, 200)
        r = self.client.get(reverse('themes') + '?p=mac')
        eq_(r.status_code, 200)

    def test_invalid_filters(self):
        """Handle invalid params gracefully."""
        r = self.client.get(reverse('themes') + '?a=somethinginvalid')
        eq_(r.status_code, 404)
