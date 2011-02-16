from django.contrib.sites.models import Site

from test_utils import eq_

from input import cron
from input.tests import InputTestCase


class TestCron(InputTestCase):
    def setUp(self):
        Site.objects.all().delete()

    def test_set_domains(self):
        Site.objects.create(pk=1, domain='hi', name='hi')
        Site.objects.create(pk=2, domain='there', name='there')
        cron.set_domains('f', 'u')
        eq_(Site.objects.get(id=1).domain, 'f')
        eq_(Site.objects.get(id=2).domain, 'u')

    def test_set_domains_no_args(self):
        Site.objects.create(pk=1, domain='hi', name='hi')
        Site.objects.create(pk=2, domain='there', name='there')
        cron.set_domains(None, None)
        # Assert NOOP
        eq_(Site.objects.get(id=1).domain, 'hi')
        eq_(Site.objects.get(id=2).domain, 'there')
