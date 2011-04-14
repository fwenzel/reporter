import datetime
import socket

from mock import patch
from nose.tools import eq_

import input
from feedback.models import Opinion
from search.client import Client, SearchError, extract_filters
from search.tests import SphinxTestCase

query = lambda x='', **kwargs: Client().query(x, **kwargs)
num_results = lambda x='', **kwargs: len(query(x, **kwargs))


class SearchTest(SphinxTestCase):
    def test_default_ordering(self):
        """Any query should return results in rev-chron order."""
        r = query()
        dates = [o.created for o in r]
        eq_(dates, sorted(dates, reverse=True), "These aren't revchron.")

        r = query('Firefox')
        dates = [o.created for o in r]
        eq_(dates, sorted(dates, reverse=True), "These aren't revchron.")

    @patch('search.client.sphinx.SphinxClient.RunQueries')
    def test_errors(self, sphinx):
        for error in (socket.timeout(), Exception(),):
            sphinx.side_effect = error
            self.assertRaises(SearchError, query)

    def test_filter_date(self):
        start = datetime.datetime(2010, 5, 27)
        end = datetime.datetime(2010, 5, 27)
        eq_(num_results(date_start=start, date_end=end), 5)

    def test_filter_locale(self):
        start = datetime.datetime(2010, 5, 27)
        eq_(num_results(locale='en-US', date_start=start), 29)
        eq_(num_results(locale='de', date_start=start), 1)
        eq_(num_results(locale='unknown', date_start=start), 1)

    def test_filter_platform(self):
        start = datetime.datetime(2010, 5, 27)
        eq_(num_results(platform='mac', date_start=start), 31)
        eq_(num_results(platform='palm', date_start=start), 0)

    def test_filter_product(self):
        start = datetime.datetime(2010, 5, 27)
        eq_(num_results(product=1, date_start=start), 31)
        eq_(num_results(product=2, date_start=start), 0)

    def test_filter_type(self):
        start = datetime.datetime(2010, 5, 27)
        eq_(num_results(type=input.OPINION_PRAISE.id, date_start=start), 17)
        eq_(num_results(type=input.OPINION_ISSUE.id, date_start=start), 11)
        eq_(num_results(type=input.OPINION_IDEA.id, date_start=start), 3)

    def test_filter_version(self):
        start = datetime.datetime(2010, 5, 27)
        eq_(num_results(version='3.6.3', date_start=start), 11)
        eq_(num_results(version='3.6.4', date_start=start), 16)

    @patch('search.client.sphinx.SphinxClient.GetLastError')
    def test_getlasterror(self, sphinx):
        sphinx = lambda: True
        self.assertRaises(SearchError, query)

    def test_query(self):
        start = datetime.datetime(2010, 5, 27)
        eq_(num_results(date_start=start), 31)

    @patch('search.client.sphinx.SphinxClient.RunQueries')
    def test_result_empty(self, rq):
        """
        If sphinx has no results, but gives us a weird result, let's return an
        empty list.
        """
        rq.return_value = [dict(error=None)]
        eq_(query(), [])

    @patch('search.client.sphinx.SphinxClient.RunQueries')
    def test_result_errors(self, rq):
        """
        If sphinx tells us there's an error, make sure we raise a
        SearchError.
        This is unexpected, so we mock the behavior.
        """
        rq.return_value = [dict(error='you lose')]
        self.assertRaises(SearchError, query)

    def test_result_set(self):
        start = datetime.datetime(2010, 5, 27)
        rs = query(date_start=start)
        assert isinstance(rs[0], Opinion)

    def test_url_search(self):
        start = datetime.datetime(2010, 5, 27)
        eq_(num_results('url:*', date_start=start), 7)


def test_date_filter_timezone():
    """Ensure date filters are applied in app time (= PST), not UTC."""
    dates = dict(date_start=datetime.date(2010, 1, 1),
                 date_end=datetime.date(2010, 1, 31))
    _, ranges, _ = extract_filters(dates)
    eq_(ranges['created'][0], 1262332800)  # 8:00 UTC on 1/1/2010
    # 8:00 UTC on 2/1/2010 (sic, to include all of the last day)
    eq_(ranges['created'][1], 1265011200)


def test_extract_filters_unknown():
    """
    Test that we return the proper value of unknown that sphinx is expecting.
    """
    _, _, metas = extract_filters(dict(platform='unknown'))
    eq_(metas['platform'], 0)
