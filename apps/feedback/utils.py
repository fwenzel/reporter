import re

from product_details import languages

from . import BROWSERS
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
    os_patterns = (
        ('Win32', 'win'),
        ('Mac', 'mac'),
        ('Linux', 'linux'),
    )
    os = 'other'
    for pattern in os_patterns:
        if ua.find(pattern[0]) >= 0:
            os = pattern[1]
            break
    detected['os'] = os

    # Detect locale
    info_match = re.match(r'Mozilla[^(]+\(([^)]+)\).*$', ua)
    info = [ i.strip() for i in info_match.group(1).split(';') ]
    locale = None
    for i in info:
        if i in languages:
            locale = i
            break
    detected['locale'] = locale

    return detected
