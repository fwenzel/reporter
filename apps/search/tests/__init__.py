import os
import shutil

from django.conf import settings

import test_utils
from nose import SkipTest

from search.utils import start_sphinx, stop_sphinx, reindex


# TODO(davedash): liberate from Zamboni
class SphinxTestCase(test_utils.TransactionTestCase):
    """
    This test case type can setUp and tearDown the sphinx daemon.  Use this
    when testing any feature that requires sphinx.
    """
    fixtures = ('feedback/opinions',)
    sphinx = True
    sphinx_is_running = False

    def setUp(self):
        super(SphinxTestCase, self).setUp()

        settings.SITE_ID = settings.DESKTOP_SITE_ID

        if not SphinxTestCase.sphinx_is_running:
            if (not settings.SPHINX_SEARCHD or
                not settings.SPHINX_INDEXER):  # pragma: no cover
                raise SkipTest()

            os.environ['DJANGO_ENVIRONMENT'] = 'test'

            if os.path.exists(settings.TEST_SPHINX_CATALOG_PATH):
                shutil.rmtree(settings.TEST_SPHINX_CATALOG_PATH)
            if os.path.exists(settings.TEST_SPHINX_LOG_PATH):
                shutil.rmtree(settings.TEST_SPHINX_LOG_PATH)

            os.makedirs(settings.TEST_SPHINX_LOG_PATH)
            os.makedirs(settings.TEST_SPHINX_CATALOG_PATH)

            reindex()
            start_sphinx()
            SphinxTestCase.sphinx_is_running = True

    @classmethod
    def tearDownClass(cls):
        if SphinxTestCase.sphinx_is_running:
            stop_sphinx()
            SphinxTestCase.sphinx_is_running = False
