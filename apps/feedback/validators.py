import string

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags

import product_details

import swearwords

from . import FIREFOX, MOBILE
from .utils import ua_parse
from .version_compare import version_dict


LATEST_BETAS = {
    FIREFOX: product_details.firefox_versions['LATEST_FIREFOX_DEVEL_VERSION'],
    MOBILE: product_details.mobile_details['beta_version'],
}


def validate_ua(ua):
    """Ensure a UA string represents a valid latest beta version."""
    parsed = ua_parse(ua)
    if not parsed:
        raise ValidationError('User agent string was not recognizable.')

    # compare to latest beta, if UA enforced.
    if settings.ENFORCE_USER_AGENT:
        ref_version = version_dict(LATEST_BETAS[parsed['browser']])
        this_version = version_dict(parsed['version'])

        # version parts to compare between reference version and this version.
        # check major and minor versions always
        version_parts = ['major', 'minor1', 'minor2']
        # if reference is a full-fledged beta version (e.g., 3.6b5), check beta
        # status and beta version as well.
        if ref_version['alpha'] and ref_version['alpha_ver']:
            version_parts += ['alpha', 'alpha_ver']

        for version_part in version_parts:
            if ref_version[version_part] != this_version[version_part]:
                raise ValidationError('Submitted User Agent is not the '
                                      'latest beta version.')


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


def validate_no_html(str):
    """Disallow HTML."""
    if strip_tags(str) != str:
        raise ValidationError('Feedback must not contain HTML.')
