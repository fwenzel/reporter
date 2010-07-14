from calendar import timegm
from datetime import timedelta
import socket

from django.conf import settings

from tower import ugettext as _

from reporter.utils import crc32, manual_order
from feedback.models import Opinion

from . import sphinxapi as sphinx


SPHINX_HARD_LIMIT = 1000  # A hard limit that sphinx imposes.


class SearchError(Exception):
    pass


class Client():

    def __init__(self):
        self.sphinx = sphinx.SphinxClient()
        self.sphinx.SetServer(settings.SPHINX_HOST, settings.SPHINX_PORT)

    def query(self, term, **kwargs):
        """Submits formatted query, retrieves ids, returns Opinions."""
        sc = self.sphinx
        sc.SetLimits(0, SPHINX_HARD_LIMIT)

        if isinstance(kwargs.get('product'), int):
            sc.SetFilter('product', (kwargs['product'],))

        if kwargs.get('version'):
            sc.SetFilter('version', (crc32(kwargs['version']),))

        if isinstance(kwargs.get('positive'), int):
            sc.SetFilter('positive', (kwargs['positive'], ))

        if kwargs.get('os'):
            sc.SetFilter('os', (crc32(kwargs['os']),))

        if kwargs.get('locale'):
            if kwargs['locale'] == 'unknown':
                sc.SetFilter('locale', (crc32(''),))
            else:
                sc.SetFilter('locale', (crc32(kwargs['locale']),))

        if kwargs.get('date_end') and kwargs.get('date_start'):
            start = int(timegm(kwargs['date_start'].timetuple()))
            end_date = kwargs['date_end'] + timedelta(days=1)
            end = int(timegm(end_date.timetuple()))
            sc.SetFilterRange('created', start, end)

        try:
            result = sc.Query(term, 'opinions')
        except socket.timeout:
            raise SearchError(_("Query has timed out."))
        except Exception, e:
            raise SearchError(_("Sphinx threw an unknown exception: %s") % e)

        if sc.GetLastError():
            raise SearchError(sc.GetLastError())

        opinion_ids = [m['id'] for m in result['matches']]
        opinions = manual_order(Opinion.objects.all(), opinion_ids)
        return opinions
