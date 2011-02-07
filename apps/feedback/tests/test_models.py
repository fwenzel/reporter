from datetime import date

from mock import patch
from test_utils import eq_, TestCase

from feedback import FIREFOX, WINDOWS_7
from feedback.models import Opinion, Term
from feedback.stats import frequent_terms


class TermTestCase(TestCase):
    fixtures = ['feedback/opinions']

    def setUp(self):
        self.split_date = date(2010, 6, 18)
        ops1 = Opinion.objects.no_cache().filter(
            created__lt=self.split_date)
        ops2 = Opinion.objects.no_cache().filter(
            created__gte=self.split_date)
        self.t1 = Term(term='Hello')
        self.t1.save()
        self.t2 = Term(term='World')
        self.t2.save()
        for o in ops1:
            o.terms.add(self.t1)
        for o in ops2:
            o.terms.add(self.t2)

    def tearDown(self):
        Term.objects.all().delete()

    def test_frequent_from_opinions(self):
        """Test frequent term listing based on opinions queryset."""
        ops = Opinion.objects.no_cache()
        ts = Term.objects.frequent(ops)
        assert ts.count() > 0

    def test_frequent_by_date(self):
        """Test frequent terms by date."""
        ts = Term.objects.frequent(date_end=self.split_date)
        eq_(ts[0].term, self.t1.term)

        ts = Term.objects.frequent(date_start=self.split_date)
        eq_(ts[0].term, self.t2.term)

    def test_frequent_stats(self):
        """Test frequent terms weights."""
        ts = Term.objects.frequent()
        freq = frequent_terms(qs=ts)
        eq_(len(freq), 2)

    def test_unicode(self):
        """Term's unicode representation."""
        t = Term(term='Hello')
        eq_(unicode(t), u'Hello')


@patch('django.db.models.query.QuerySet.filter')
def test_opinion_manager_between(filter):
    """Ensure date filters are applied by ``between`` manager."""
    Opinion.objects.between(date_start=date(2011, 1, 1))
    filter.assert_called_with(created__gte=date(2011, 1, 1))

    Opinion.objects.between(date_start=date(2011, 1, 1))
    filter.assert_called_with(created__gte=date(2011, 1, 1))


def test_product_name():
    """Show product name or ID if unknown."""
    o = Opinion()
    o.product = FIREFOX.id
    eq_(o.product_name, FIREFOX.pretty)

    o.product = 17  # Unknown ID
    eq_(o.product_name, 17)


def test_os_name():
    """Show platform name or ID if unknown."""
    o = Opinion()
    o.os = 'win7'
    eq_(o.os_name, WINDOWS_7.pretty)

    o.os = 'win25'  # Unknown ID
    eq_(o.os_name, 'win25')
