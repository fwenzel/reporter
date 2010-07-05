import os
import shutil
import time
import datetime

from django.conf import settings

from nose.tools import eq_
import test_utils

from search.client import Client
from search.utils import start_sphinx, stop_sphinx, reindex


# TODO(davedash): liberate from Zamboni
class SphinxTestCase(test_utils.TransactionTestCase):
    """
    This test case type can setUp and tearDown the sphinx daemon.  Use this
    when testing any feature that requires sphinx.
    """

    fixtures = ['feedback/opinions']
    sphinx = True
    sphinx_is_running = False

    def setUp(self):
        super(SphinxTestCase, self).setUp()

        if not SphinxTestCase.sphinx_is_running:
            if (not settings.SPHINX_SEARCHD or
                not settings.SPHINX_INDEXER):  # pragma: no cover
                raise SkipTest()

            os.environ['DJANGO_ENVIRONMENT'] = 'test'

            # XXX: Path names need to be more clear.
            if os.path.exists(settings.SPHINX_CATALOG_PATH):
                shutil.rmtree(settings.SPHINX_CATALOG_PATH)
            if os.path.exists(settings.SPHINX_LOG_PATH):
                shutil.rmtree(settings.SPHINX_LOG_PATH)

            os.makedirs(settings.SPHINX_LOG_PATH)
            os.makedirs(settings.SPHINX_CATALOG_PATH)

            reindex()
            start_sphinx()
            time.sleep(1)
            SphinxTestCase.sphinx_is_running = True

    @classmethod
    def tearDownClass(cls):
        if SphinxTestCase.sphinx_is_running:
            stop_sphinx()
            SphinxTestCase.sphinx_is_running = False


query = lambda x='', **kwargs: Client().query(x, **kwargs)
num_results = lambda x='', **kwargs: len(query(x, **kwargs))
class SearchTest(SphinxTestCase):

    def test_query(self):
        eq_(num_results(), 28)

    def test_product_filter(self):
        eq_(num_results(product=1), 28)
        eq_(num_results(product=2), 0)

    def test_version_filter(self):
        eq_(num_results(version='3.6.3'), 11)
        eq_(num_results(version='3.6.4'), 16)

    def test_positive_filter(self):
        eq_(num_results(positive=1), 17)
        eq_(num_results(positive=0), 11)

    def test_os_filter(self):
        eq_(num_results(os='mac'), 28)
        eq_(num_results(os='palm'), 0)

    def test_locale_filter(self):
        eq_(num_results(locale='en-US'), 26)
        eq_(num_results(locale='de'), 1)

    def test_date_filter(self):
        start = datetime.datetime(2010, 5, 27)
        end = datetime.datetime(2010, 5, 28)
        eq_(num_results(date_start=start, date_end=end), 5)
        pass
