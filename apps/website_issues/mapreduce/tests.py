import sys
import bz2
import StringIO

import test_utils
from nose.tools import eq_
from dumbo.backends.common import MapRedBase
from dumbo.lib import identitymapper
from django.utils.functional import memoize
from django.core.management import call_command

from website_issues.mapreduce import tasks
from website_issues.mapreduce import generate_sites


TEST_FILE = "lib/website_issues/test_opinions.tsv"


def _dumbo_mixin(cls):
    """Emulates dumbo metraprogramming."""
    return type("DumboMapper", (cls, MapRedBase), {})


def _map(mapper, input_pairs):
    """Simulate the hadoop M/R map phase."""
    buckets = {}
    def put(k, v):
        if not k in buckets: buckets[k] = []
        buckets[k].append(values)

    with Silence():
        try:
            for key, values in mapper(input_pairs):
                put(key, values)
        except TypeError:
            for in_key, in_value in input_pairs:
                for key, values in mapper(in_key, in_value):
                    put(key, values)
    return buckets


def _shuffle(buckets):
    """Simulate the hadoop M/R shuffle (sort) phase."""
    for key in sorted(buckets.iterkeys()):
        yield (key, buckets[key])


def _reduce(reducer, bucket_list):
    """Simulate the hadoop M/R reduce phase."""
    output_pairs = []
    with Silence():
        for key, values in bucket_list:
            for result in reducer(key, values):
                output_pairs.append(result)
    return output_pairs


class Silence(object):
    """Used to suppress noisy counters."""
    def __enter__(self):
        self._true_stderr = sys.stderr
        sys.stderr = StringIO.StringIO()

    def __exit__(self, exc_type, exc_value, exc_tb):
        if exc_type is not None:
            for line in sys.stderr: self._true_stderr.write(line)
        sys.stderr = self._true_stderr


class TestTasks(test_utils.TestCase):

    def _input_pairs(self, lines):
        """Generate mock (key, value) pairs for file-like input"""
        i = 0
        for line in lines:
            yield (i, line[:-1])
            i += len(line)

    # mapreduce iteration 0
    def _summaries(self):
        tsv_input = open(TEST_FILE)
        mapper = _dumbo_mixin(tasks.SiteSummaryMapper)()
        return _map(mapper, self._input_pairs(tsv_input))

    def test_sitesummary_mapper(self):
        buckets = self._summaries()
        eq_(len(buckets.keys()), 97)
        all_values = []
        for values in buckets.values():
            all_values.extend(values)
        eq_(len(all_values), 111)

    # mapreduce iteration 1
    def _clusters(self):
        bucket_list = _shuffle(self._summaries())
        reducer = _dumbo_mixin(tasks.CommentClusteringReducer)()
        return _reduce(reducer, bucket_list)

    def test_comment_clustering_reducer(self):
        pairs = self._clusters()
        eq_(len(pairs), 258)

    # mapreduce iteration 2
    def _clusters_with_ids(self):
        pairs = self._clusters()
        bucket_list = _shuffle(_map(identitymapper, pairs))
        reducer = _dumbo_mixin(tasks.ClusterIdReducer)()
        return _reduce(reducer, bucket_list)

    def test_cluster_id_reducer(self):
        pairs = self._clusters_with_ids()
        eq_(len(pairs), 258)

    # mapreduce iteration 3
    def _summaries_with_sizes(self):
        pairs = self._clusters_with_ids()
        bucket_list = _shuffle(_map(identitymapper, pairs))
        reducer = _dumbo_mixin(tasks.SummarySizeReducer)()
        return _reduce(reducer, bucket_list)

    def test_summary_size_reducer(self):
        pairs = self._summaries_with_sizes()
        eq_(len(pairs), 258)

    # mapreduce iteration 4
    def _summaries_with_ids(self):
        pairs = self._summaries_with_sizes()
        bucket_list = _shuffle(_map(identitymapper, pairs))
        reducer = _dumbo_mixin(tasks.SummaryIdReducer)()
        return _reduce(reducer, bucket_list)

    def test_sitesummary_id_reducer(self):
        pairs = self._summaries_with_ids()
        eq_(len(pairs), 258)

    # mapreduce iteration 5
    def _denormalized(self):
        pairs = self._summaries_with_ids()
        bucket_list = _shuffle(_map(identitymapper, pairs))
        reducer = _dumbo_mixin(tasks.DenormalizingReducer)()
        return _reduce(reducer, bucket_list)

    def test_denormalizing_reducer(self):
        pairs = self._denormalized()
        eq_(len(pairs), 258)
