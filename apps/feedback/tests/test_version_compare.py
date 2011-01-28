import copy

from nose.tools import eq_
import test_utils

from feedback.version_compare import (simplify_version, version_dict,
                                      version_int, version_list)


class VersionCompareTest(test_utils.TestCase):
    def test_simplify_version(self):
        """Make sure version simplification works."""
        versions = {
            '4.0b1': '4.0b1',
            '3.6': '3.6',
            '3.6.4b1': '3.6.4b1',
            '3.6.4build1': '3.6.4',
            '3.6.4build17': '3.6.4',
        }
        for v in versions:
            self.assertEquals(simplify_version(v), versions[v])

    def test_dict_vs_int(self):
        """
        version_dict and _int can use each other's data but must not overwrite
        it.
        """
        version_string = '4.0b8pre'
        dict1 = copy.copy(version_dict(version_string))
        int1 = version_int(version_string)
        dict2 = version_dict(version_string)
        int2 = version_int(version_string)
        eq_(dict1, dict2)
        eq_(int1, int2)


def test_version_filter():
    """Test if version lists are generated properly."""
    my_versions = {
        '4.0b2build8': '2010-12-06',
        '3.0': '2010-12-01',
        '4.0b1': '2010-11-24',
        '4.0b2build7': '2010-12-05',
    }
    expected = ('4.0b2', '4.0b1')

    test_list = version_list(my_versions, hide_below='4.0b1')

    # Check if the generated version list is the same as we expect.
    eq_(len(expected), len(test_list))
    for n, v in enumerate(test_list):
        eq_(v, expected[n])
