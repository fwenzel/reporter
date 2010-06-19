import re

from django.conf import settings

import product_details
from topia.termextract import extract

from . import BROWSERS, OS_OTHER, OS_PATTERNS
from .decorators import cached


@cached()
def ua_parse(ua):
    """
    Simple user agent string parser for Firefox and friends.

    returns {
        browser: .FIREFOX or .MOBILE,
        version: '3.6b4' or similar,
        os: one of ('mac', 'win', 'linux', 'other'),
        locale: locale code matching locale_details, else None
        }
    or None if detection failed.
    """

    if not ua:
        return None

    # Detect browser
    detected = {}
    for browser in BROWSERS:
        match = re.match(browser[1], ua)
        if match:
            detected = {
                'browser': browser[0],
                'version': match.group(2),
            }
            break
    # Browser not recognized? Bail.
    if not detected:
        return None

    # Detect OS
    os = OS_OTHER.short
    for pattern in OS_PATTERNS:
        if ua.find(pattern[0]) >= 0:
            os = pattern[1]
            break
    detected['os'] = os

    # Detect locale
    info_match = re.match(r'Mozilla[^(]+\(([^)]+)\).*$', ua)
    info = [ i.strip() for i in info_match.group(1).split(';') ]
    locale = None
    for i in info:
        if i in product_details.languages:
            locale = i
            break
    detected['locale'] = locale

    return detected


def extract_terms(text):
    """
    Use topia.termextract to perform a simple tag extraction from
    user comments.
    """
    extractor = extract.TermExtractor()
    # Use permissive filter to find all possibly relevant terms in short texts.
    extractor.filter = extract.permissiveFilter
    terms = extractor(text)

    # Collect terms in lower case, but only the ones that consist of single
    # words (t[2] == 1), and are at most 25 chars long.
    return [ t[0].lower() for t in terms if t[2] == 1 and
             settings.MIN_TERM_LENGTH <= len(t[0]) <= settings.MAX_TERM_LENGTH ]


def smart_truncate(content, length=100, suffix='...'):
    """Truncate text at word boundaries."""
    if len(content) <= length:
        return content
    else:
        return ' '.join(content[:length+1].split(' ')[0:-1]) + suffix
