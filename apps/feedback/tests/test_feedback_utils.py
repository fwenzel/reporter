"""Test feedback.utils."""
from django import http

from nose.tools import eq_

from input import FIREFOX, MOBILE
from feedback.utils import detect_language, ua_parse, smart_truncate


def test_ua_parse():
    """Test user agent parser for Firefox."""
    patterns = (
        # valid Fx
        ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; de; rv:1.9.2.3) '
         'Gecko/20100401 Firefox/3.6.3',
         FIREFOX, '3.6.3', 'mac'),
        ('Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.4) '
         'Gecko/20100611 Firefox/3.6.4 (.NET CLR 3.5.30729)',
         FIREFOX, '3.6.4', 'winxp'),
        # additional parentheses (bug 578339)
        ('Mozilla/5.0 (X11; U; Linux i686 (x86_64); en-US; rv:2.0b1) '
         'Gecko/20100628 Firefox/4.0b1',
         FIREFOX, '4.0b1', 'linux'),
        # locale fallback (bug 578339)
        ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; fr-FR; rv:2.0b1) '
         'Gecko/20100628 Firefox/4.0b1',
         FIREFOX, '4.0b1', 'mac'),
        ('Mozilla/5.0 (X11; U; Linux x86_64; cs-CZ; rv:2.0b2pre) Gecko/20100630 '
         'Minefield/4.0b2pre',
         FIREFOX, '4.0b2pre', 'linux'),

        # valid Fennec
        ('Mozilla/5.0 (X11; U; Linux armv6l; fr; rv:1.9.1b1pre) Gecko/'
         '20081005220218 Gecko/2008052201 Fennec/0.9pre',
         MOBILE, '0.9pre', 'linux'),
        ('Mozilla/5.0 (X11; U; FreeBSD; en-US; rv:1.9.2a1pre) '
         'Gecko/20090626 Fennec/1.0b2',
         MOBILE, '1.0b2', 'other'),
        ('Mozilla/5.0 (Maemo; Linux armv71; rv:2.0b6pre) Gecko/'
         '20100924 Namoroka/4.0b7pre Fennec/2.0b1pre',
         MOBILE, '2.0b1pre', 'maemo'),
        ('Mozilla/5.0 (Android; Linux armv71; rv:2.0b6pre) Gecko/'
         '20100924 Namoroka/4.0b7pre Fennec/2.0b1pre',
         MOBILE, '2.0b1pre', 'android'),

        # invalid
        ('A completely bogus Firefox user agent string.', None),
        ('Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; en-us) '
         'AppleWebKit/531.22.7 (KHTML, like Gecko) Version/4.0.5 '
         'Safari/531.22.7', None),
        ('Mozilla/5.0 (Windows; U; Windows NT 6.1; de; rv:1.9.2.6) '
         'Gecko/20100625 Firefox/ Anonymisiert durch AlMiSoft '
         'Browser-Anonymisierer 48771657', None),  # bug 629687
    )

    for pattern in patterns:
        parsed = ua_parse(pattern[0])
        if pattern[1]:
            eq_(parsed['browser'], pattern[1])
            eq_(parsed['version'], pattern[2])
            eq_(parsed['platform'], pattern[3])
        else:
            assert parsed is None

def test_detect_language():
    """Check Accept-Language matching for feedback submission."""
    patterns = (
        ('en-us,en;q=0.7,de;q=0.8', 'en-US'),
        ('fr-FR,de-DE;q=0.5', 'fr'),
        ('zh, en-us;q=0.8, en;q=0.6', 'en-US'),
        ('German', ''), # invalid
    )

    for pattern in patterns:
        req = http.HttpRequest()
        req.META['HTTP_ACCEPT_LANGUAGE'] = pattern[0]
        eq_(detect_language(req), pattern[1])

def test_smart_truncate():
    """Test text truncation on word boundaries."""
    patterns = (
        ('text, teeext', 10, 'text,...'),
        ('somethingreallylongwithnospaces', 10, 'somethingr...'),
        ('short enough', 12, 'short enough'),
    )
    for pattern in patterns:
        eq_(smart_truncate(pattern[0], length=pattern[1]), pattern[2])

