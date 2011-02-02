import os
import re
import socket
import time
from collections import defaultdict
from datetime import timedelta
from operator import itemgetter

from django.conf import settings

from product_details import product_details
from tower import ugettext as _

from input import (KNOWN_DEVICES, KNOWN_MANUFACTURERS, RATING_USAGE,
                   OPINION_PRAISE, OPINION_SUGGESTION)
from input.utils import crc32, manual_order
from feedback import OS_USAGE
from feedback.models import Opinion

import sphinxapi as sphinx


SPHINX_HARD_LIMIT = 1000  # A hard limit that sphinx imposes.


def collapsed(matches, trans, name):
    """
    Collapses aggregate matches into a list:
    [{name: 'foo', 'count': 1} ..., {name: 'foo2', 'count': 23}]
    """
    data = defaultdict(int)
    for result in matches:
        data[trans.get(result['attrs'][name])] += result['attrs']['count']

    return [{name: key, 'count': val} for key, val in
            sorted(data.items(), key=itemgetter(1), reverse=True)]


def sanitize_query(term):
    term = term.strip('^$ ').replace('^$', '')
    return term


def extract_filters(kwargs):
    """
    Pulls all the filtering options out of kwargs and returns dictionaries of
    filters, range filters and meta filters.
    """
    filters = {}
    ranges = {}
    metas = {}

    if isinstance(kwargs.get('product'), int):
        metas['product'] = kwargs['product']

    if kwargs.get('version'):
        filters['version'] = crc32(kwargs['version'])

    if kwargs.get('type'):
        metas['type'] = kwargs['type']

    for meta in ('os', 'manufacturer', 'device'):
        val = kwargs.get(meta)
        if val and val.lower() == 'unknown':
            # In this situation 'unknown' usually means empty.
            metas[meta] = crc32('')
        elif val:
            metas[meta] = crc32(kwargs[meta])

    if kwargs.get('locale'):
        if kwargs['locale'] == 'unknown':
            filters['locale'] = crc32('')
        else:
            filters['locale'] = crc32(kwargs['locale'])

    if kwargs.get('date_end') and kwargs.get('date_start'):
        start = int(time.mktime(kwargs['date_start'].timetuple()))
        end_date = kwargs['date_end'] + timedelta(days=1)
        end = int(time.mktime(end_date.timetuple()))
        ranges['created'] = (start, end)

    return (filters, ranges, metas)


class SearchError(Exception):
    pass


class Client(object):

    def __init__(self):
        self.sphinx = sphinx.SphinxClient()

        if os.environ.get('DJANGO_ENVIRONMENT') == 'test':
            self.sphinx.SetServer(settings.SPHINX_HOST,
                                  settings.TEST_SPHINX_PORT)
        else:  # pragma: nocover
            self.sphinx.SetServer(settings.SPHINX_HOST, settings.SPHINX_PORT)

        self.index = 'opinions'
        self.meta = {}
        self.queries = {}
        self.query_index = 0
        self.meta_filters = {}

    def add_meta_query(self, field, term):
        """Adds a 'meta' query to the client, this is an aggregate of some
        field that we can use to populate filters.

        This also adds meta filters that do not match the current query.

        E.g. if we can add back category filters to see what tags exist in
        that data set.
        """
        orig_field = field

        if '__' in field:
            (field, method, over) = field.split('__')
            select = '%s, %s(%s) as aggregate' % (field, method, over)
        else:
            select = '%s, SUM(1) as count' % field

        # We only need to select a single field for aggregate queries.
        self.sphinx.SetSelect(select)
        self.sphinx.SetLimits(0, SPHINX_HARD_LIMIT)

        self.sphinx.SetGroupBy(field, sphinx.SPH_GROUPBY_ATTR, '@count DESC')

        self.sphinx.AddQuery(term, self.index)

        self.queries[orig_field] = self.query_index
        self.query_index += 1
        self.sphinx.ResetGroupBy()


    def handle_metas(self, results, metas, kwargs):
        # Handle any meta data we have.
        if 'type' in metas:
            self.meta['type'] = self._type_meta(results, **kwargs)
        if 'locale' in metas:
            self.meta['locale'] = self._locale_meta(results, **kwargs)
        if 'os' in metas:
            self.meta['os'] = self._os_meta(results, **kwargs)
        if 'manufacturer' in metas:
            self.meta['manufacturer'] = self._manufacturer_meta(results,
                                                                **kwargs)
        if 'device' in metas:
            self.meta['device'] = self._device_meta(results, **kwargs)
        if 'day_sentiment' in metas:
            self.meta['day_sentiment'] = self._day_sentiment(results,
                                                                 **kwargs)

    def add_filter(self, field, values, meta=False):
        if not isinstance(values, (tuple, list)):
            values = (values,)

        self.sphinx.SetFilter(field, values)

    def query(self, term, limit=20, offset=0, **kwargs):
        """Submits formatted query, retrieves ids, returns Opinions."""
        sc = self.sphinx
        term = sanitize_query(term)

        # Extract and apply various filters.
        (includes, ranges, metas) = extract_filters(kwargs)

        for filter, value in includes.iteritems():
            self.add_filter(filter, value)

        for filter, value in ranges.iteritems():
            sc.SetFilterRange(filter, *value)

        for filter, value in metas.iteritems():
            self.add_filter(filter, value, meta=True)

        url_re = re.compile(r'\burl:\*\B')

        if url_re.search(term):
            parts = url_re.split(term)
            sc.SetFilter('has_url', (1,))
            term = ''.join(parts)

        if 'meta' in kwargs:
            for meta in kwargs['meta']:
                self.add_meta_query(meta, term)

        sc.SetLimits(min(SPHINX_HARD_LIMIT - limit, offset), limit)

        # Always sort in reverse chronological order.
        sc.SetSortMode(sphinx.SPH_SORT_ATTR_DESC, 'created')
        sc.AddQuery(term, self.index)
        self.queries['primary'] = self.query_index
        self.query_index += 1
        try:
            results = sc.RunQueries()
        except socket.timeout:
            raise SearchError(_("Query has timed out."))
        except Exception, e:
            # L10n: Sphinx is the name of the search engine software.
            raise SearchError(_("Sphinx threw an unknown exception: %s") % e)

        if sc.GetLastError():
            raise SearchError(sc.GetLastError())

        self.handle_metas(results, kwargs.get('meta', {}), kwargs)
        result = results[self.queries['primary']]
        self.total_found = result.get('total_found', 0) if result else 0

        if result['error']:
            raise SearchError(result['error'])

        if result and 'total' in result:
            return self.get_result_set(term, result, offset, limit)
        else:
            return []

    def _day_sentiment(self, results, **kwargs):
        result = results[self.queries['day_sentiment']]
        pos = []
        neg = []
        sug = []
        for i in result['matches']:
            day_sentiment = i['attrs']['day_sentiment']
            type = day_sentiment % 10
            count = i['attrs']['count']

            if type == OPINION_PRAISE.id:
                # Take the type out of the timestamp.  c.f. sphinx.conf.
                pos.append((day_sentiment - type, count))
            elif type == OPINION_SUGGESTION.id:
                sug.append((day_sentiment - type, count))
            else:
                neg.append((day_sentiment - type, count))

        return dict(praise=pos, issue=neg, suggestion=sug)

    def _type_meta(self, results, **kwargs):
        result = results[self.queries['type']]
        return [(f['attrs']) for f in result.get('matches', [])]

    def _os_meta(self, results, **kwargs):
        result = results[self.queries['os']]
        t = dict(((crc32(f.short), f.short) for f in OS_USAGE))
        return [dict(count=f['attrs']['count'], os=t.get(f['attrs']['os']))
                for f in result['matches']]

    def _manufacturer_meta(self, results, **kwargs):
        result = results[self.queries['manufacturer']]
        t = dict(((crc32(m), m) for m in KNOWN_MANUFACTURERS))
        return collapsed(result['matches'], t, 'manufacturer')

    def _device_meta(self, results, **kwargs):
        result = results[self.queries['device']]
        t = dict(((crc32(d), d) for d in KNOWN_DEVICES))
        return collapsed(result['matches'], t, 'device')

    def _locale_meta(self, results, **kwargs):
        result = results[self.queries['locale']]
        if 'matches' in result:
            t = dict(((crc32(f), f) for f in product_details.languages))
            return [dict(count=f['attrs']['count'],
                         locale=t.get(f['attrs']['locale']))
                    for f in result['matches']]

    def get_result_set(self, term, result, offset, limit):
        # Return results as a ResultSet of opinions
        opinion_ids = [m['id'] for m in result['matches']]
        opinions = manual_order(Opinion.objects.all(), opinion_ids)
        return ResultSet(opinions, self.total_found, offset)


class ResultSet(object):
    """
    ResultSet wraps around a query set and provides meta data used for
    pagination.
    """
    def __init__(self, queryset, total, offset):
        self.queryset = queryset
        self.total = total
        self.offset = offset

    def __len__(self):
        return self.total

    def __iter__(self):
        return iter(self.queryset)

    def __getitem__(self, k):
        """
        ``__getitem__`` gets the elements specified by doing ``rs[k]`` where
        ``k`` is a slice (e.g. ``1:2``) or an integer.

        ``queryset`` doesn't contain all ``total`` items, just the items for
        the current page, so we need to adjust ``k``
        """
        if isinstance(k, slice) and k.start >= self.offset:
            k = slice(k.start - self.offset, k.stop - self.offset)
        elif isinstance(k, int):
            k -= self.offset

        return self.queryset.__getitem__(k)


class RatingsClient(Client):
    """Queries the ratings index instead."""

    def __init__(self):
        super(RatingsClient, self).__init__()
        self.index = 'ratings'

    def handle_metas(self, results, metas, kwargs):
        super(RatingsClient, self).handle_metas(results, metas, kwargs)
        if 'startup' in metas:
            self.meta['ratings'] = self._ratings_meta(results, **kwargs)
            self.meta['ratings_avg'] = self._ratings_avg_meta(results,
                                                              **kwargs)

    def _ratings_meta(self, results, **kwargs):
        agg = {}
        for rating in RATING_USAGE:
            d = defaultdict(int)
            d.update((m['attrs'][rating.short], m['attrs']['count'])
                     for m in results[self.queries[rating.short]]['matches'])
            agg[rating.id] = d
        return agg

    def _ratings_avg_meta(self, results, **kwargs):
        agg = {}
        for rating in RATING_USAGE:
            result = results[self.queries['day__avg__%s' % rating.short]]
            value = lambda m: round(m['attrs']['aggregate'], 1)
            agg[rating.id] = [(m['attrs']['day'], value(m)) for m
                              in result['matches']]
        return agg
