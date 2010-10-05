from calendar import timegm
from datetime import timedelta
import os
import re
import socket

from django.conf import settings

from tower import ugettext as _

from input.utils import crc32, manual_order
from feedback.models import Opinion

from . import sphinxapi as sphinx


SPHINX_HARD_LIMIT = 1000  # A hard limit that sphinx imposes.


def sanitize_query(term):
    term = term.strip('^$ ').replace('^$', '')
    return term


class SearchError(Exception):
    pass


class Client():

    def __init__(self):
        self.sphinx = sphinx.SphinxClient()

        if os.environ.get('DJANGO_ENVIRONMENT') == 'test':
            self.sphinx.SetServer(settings.SPHINX_HOST,
                                  settings.TEST_SPHINX_PORT)
        else:
            self.sphinx.SetServer(settings.SPHINX_HOST, settings.SPHINX_PORT)

    def query(self, term, **kwargs):
        """Submits formatted query, retrieves ids, returns Opinions."""
        sc = self.sphinx
        sc.SetLimits(0, SPHINX_HARD_LIMIT)

        # Always sort in reverse chronological order.
        sc.SetSortMode(sphinx.SPH_SORT_ATTR_DESC, 'created')

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

        url_re = re.compile(r'\burl:\*\B')

        if url_re.search(term):
            parts = url_re.split(term)
            sc.SetFilter('has_url', (1,))
            term = ''.join(parts)

        try:
            result = sc.Query(sanitize_query(term), 'opinions')
        except socket.timeout:
            raise SearchError(_("Query has timed out."))
        except Exception, e:
            # L10n: Sphinx is the name of the search engine software.
            raise SearchError(_("Sphinx threw an unknown exception: %s") % e)

        if sc.GetLastError():
            raise SearchError(sc.GetLastError())

        opinion_ids = [m['id'] for m in result['matches']]
        opinions = manual_order(Opinion.objects.all(), opinion_ids)
        return opinions
