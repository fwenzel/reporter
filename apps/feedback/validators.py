import string

from django.conf import settings
from django.core.exceptions import ValidationError

from product_details import firefox_versions, mobile_details

import swearwords

from . import FIREFOX, MOBILE
from .utils import ua_parse
from .version_compare import version_int


LATEST_BETAS = {
    FIREFOX: firefox_versions['LATEST_FIREFOX_DEVEL_VERSION'],
    MOBILE: mobile_details['beta_version'],
}


def validate_ua(ua):
    """Ensure a UA string represents a valid latest beta version."""
    parsed = ua_parse(ua)
    if not parsed:
        return ValidationError('User agent string was not recognizable.')

    # compare to latest beta, if UA enforced.
    if settings.ENFORCE_USER_AGENT:
        ref_version = LATEST_BETAS[parsed['browser']]
        if (version_int(ref_version) != version_int(parsed['version'])):
            raise ValidationError(
                'Submitted User Agent is not the latest beta version.')


def validate_swearwords(str):
    """Soft swear word filter to encourage contructive feedback."""
    words = set([ s.strip(string.punctuation) for s in str.split() ])
    matches = words.intersection(swearwords.WORDLIST)
    if matches:
        raise ValidationError(
            'Your comments contains swear words (%s). In order to help us '
            'improve our products, please use words that help us create an '
            'action or to-do from your constructive feedback. Thanks!' % (
                ', '.join(matches)))
