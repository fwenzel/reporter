import datetime
import socket

from mock import patch
from nose.tools import eq_

import input
from feedback.models import Opinion
from search.client import Client, RatingsClient, SearchError, extract_filters
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
        eq_(num_results(locale='en-US'), 29)
        eq_(num_results(locale='de'), 1)
        eq_(num_results(locale='unknown'), 1)

    def test_filter_platform(self):
        eq_(num_results(platform='mac'), 31)
        eq_(num_results(platform='palm'), 0)

    def test_filter_product(self):
        eq_(num_results(product=1), 31)
        eq_(num_results(product=2), 0)

    def test_filter_type(self):
        eq_(num_results(type=input.OPINION_PRAISE.id), 17)
        eq_(num_results(type=input.OPINION_ISSUE.id), 11)
        eq_(num_results(type=input.OPINION_IDEA.id), 3)

    def test_filter_version(self):
        eq_(num_results(version='3.6.3'), 11)
        eq_(num_results(version='3.6.4'), 16)

    @patch('search.client.sphinx.SphinxClient.GetLastError')
    def test_getlasterror(self, sphinx):
        sphinx = lambda: True
        self.assertRaises(SearchError, query)

    def test_meta_query(self):
        """Test that we can store complicated filter queries."""
        c = RatingsClient()
        c.query('', meta=['day__avg__startup', 'startup'])
        assert 'day__avg__startup' in c.queries

    def test_query(self):
        eq_(num_results(), 31)

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
        rs = query()
        assert isinstance(rs[0], Opinion)

    def test_url_search(self):
        eq_(num_results('url:*'), 7)


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
