from test_utils import eq_

from feedback.helpers import locale_name, smiley


def test_locale_name():
    eq_(locale_name('de'), 'German')
    eq_(locale_name('de', native=True), 'Deutsch')
    eq_(locale_name('omg'), 'Unknown')

def test_smiley():
    assert smiley('happy').find('span') >= 0
    assert smiley('sad').find('span') >= 0
    eq_(smiley('cheesecake'), '')
