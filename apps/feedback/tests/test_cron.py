import test_utils
from nose.tools import eq_

import input
from feedback.cron import populate, DEFAULT_NUM_OPINIONS
from feedback.models import Opinion


class TestPopulate(test_utils.TestCase):
    def test_populate(self):
        populate()
        eq_(Opinion.objects.count(), DEFAULT_NUM_OPINIONS)

    def test_populate_type(self):
        populate(DEFAULT_NUM_OPINIONS, 'desktop', input.OPINION_IDEA)
        count = Opinion.objects.filter(
                type=input.OPINION_IDEA.id).count()
        eq_(count, DEFAULT_NUM_OPINIONS)
