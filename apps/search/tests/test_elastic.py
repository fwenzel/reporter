"""
These tests specifically test elasticsearch related things.

Specifically:

    * creating an opinion will add it to the elastic search index.
    * deleteing an opinion will remove it from the index.
"""

from elasticutils.tests import ESTestCase
from elasticutils import S
from nose.tools import eq_

from feedback.models import Opinion


class TestElastic(ESTestCase):
    def test_index(self):
        o = Opinion.objects.create(
                product=1,
                description='Get me a chocolate milk, with extra salt.')
        self.es.refresh()
        eq_(len(S('chocolate')), 1)
        return o

    def test_delete(self):
        a = self.test_index()
        a.delete()
        self.es.refresh()
        eq_(len(S('chocolate')), 0, 'We deleted this... WTF?')
