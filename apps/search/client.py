import socket
import time

from django.conf import settings

import sphinxapi as sphinx
from reporter.utils import crc32, manual_order
from feedback.models import Opinion

SPHINX_HARD_LIMIT = 1000  # A hard limit that sphinx imposes.


class SearchError(Exception):
    pass


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
        """`queryset` doesn't contain all `total` items, just the items for the
        current page, so we need to adjust `k`"""
        if isinstance(k, slice) and k.start >= self.offset:
            k = slice(k.start - self.offset, k.stop - self.offset)
        elif isinstance(k, int):
            k -= self.offset

        return self.queryset.__getitem__(k)


class Client():

    def __init__(self):
        self.sphinx = sphinx.SphinxClient()
        self.sphinx.SetServer(settings.SPHINX_HOST, settings.SPHINX_PORT)

    def query(self, term, limit=5, page=1, **kwargs):
        """Submits formatted query, retrieves ids, returns Opinions."""
        sc = self.sphinx

        offset = (page - 1) * limit
        sc.SetLimits(offset, limit)

        if isinstance(kwargs.get('product'), int):
            sc.SetFilter('product', (kwargs['product'],))

        if kwargs.get('version'):
            sc.SetFilter('version', (crc32(kwargs['version']),))

        if isinstance(kwargs.get('positive'), int):
            sc.SetFilter('positive', (kwargs['positive'], ))

        if kwargs.get('os'):
            sc.SetFilter('os', (crc32(kwargs['os']),))

        if kwargs.get('locale'):
            sc.SetFilter('locale', (crc32(kwargs['locale']),))

        if kwargs.get('date_end') and kwargs.get('date_start'):
            start = int(time.mktime(kwargs['date_start'].timetuple()))
            end = int(time.mktime(kwargs['date_end'].timetuple()))
            sc.SetFilterRange('created', start, end)

        try:
            result = sc.Query(term, 'opinions')
        except socket.timeout:
            raise SearchError("Query has timed out.")
        except Exception, e:
            raise SearchError("Sphinx threw an unknown exception: %s" % e)

        if sc.GetLastError():
            raise SearchError(sc.GetLastError())


        opinion_ids = [m['id'] for m in result['matches']]
        addons = manual_order(Opinion.objects.all(), opinion_ids)
        total_found = result['total_found']

        return ResultSet(addons, min(total_found, SPHINX_HARD_LIMIT),
                         offset)
