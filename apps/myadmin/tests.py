from django.contrib.auth.models import User

import test_utils
from nose.tools import eq_

from input.urlresolvers import reverse


class ViewTestCase(test_utils.TestCase):
    def setUp(self):
        u = User.objects.create(is_superuser=True, is_staff=True, username='a')
        u.set_password('b')
        u.save()
        assert self.client.login(username='a', password='b')

    def test_export_tsv(self):
        r = self.client.get(reverse('myadmin.export_tsv'))
        eq_(r.status_code, 200)

    def test_export_tsv_post(self):
        r = self.client.post(reverse('myadmin.export_tsv'))
        eq_(r.status_code, 200)

    def test_logged_out(self):
        self.client.logout()
        r = self.client.get(reverse('myadmin.settings'))
        eq_(r.status_code, 200)

    def test_recluster(self):
        r = self.client.get(reverse('myadmin.recluster'))
        eq_(r.status_code, 200)

    def test_recluster_post(self):
        r = self.client.post(reverse('myadmin.recluster'))
        eq_(r.status_code, 302)

    def test_settings(self):
        r = self.client.get(reverse('myadmin.settings'))
        eq_(r.status_code, 200)
