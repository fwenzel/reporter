# -*- coding: utf-8 -*-
import tempfile
import os.path

from django.conf import settings

from mock import patch
import test_utils
from test_utils import eq_

import api.cron
from api.cron import _fix_row, _split_queryset, export_tsv


def test_fix_row():
    """Ensure encoding and line breaks are fixed properly."""
    data = [u"Hello\r\nWörld", 42]
    expected = [u"Hello\nWörld".encode('utf-8'), 42]
    eq_(_fix_row(data), expected)


def test_split_queryset():
    """Split a queryset into pieces."""
    # Mock queryset object: List with qs-style count function.
    class MockQs(list):
        def count(self):
            return len(self)

    bucket_size = api.cron.BUCKET_SIZE
    try:
        api.cron.BUCKET_SIZE = 10

        my_qs = MockQs(range(100))
        splits = list(_split_queryset(my_qs))
        eq_(len(splits), 10)
    finally:
        api.cron.BUCKET_SIZE = bucket_size


class ExportTestCase(test_utils.TestCase):
    fixtures = ['feedback/opinions']

    def test_export_tsv(self):
        """Export some test data, make sure export file is created."""
        old_export_dir = settings.TSV_EXPORT_DIR
        bucket_size = api.cron.BUCKET_SIZE
        try:
            settings.TSV_EXPORT_DIR = tempfile.gettempdir()
            api.cron.BUCKET_SIZE = 1

            export_tsv()
            opinions_path = os.path.join(settings.TSV_EXPORT_DIR,
                                         'opinions.tsv.bz2')
            # Make sure there is some data available. 30 bytes is a guess.
            assert os.path.getsize(opinions_path) > 30
        finally:
            settings.TSV_EXPORT_DIR = old_export_dir
            api.cron.BUCKET_SIZE = bucket_size
