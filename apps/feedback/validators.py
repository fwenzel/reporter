import re
import string

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags

import product_details

import swearwords

from . import FIREFOX, MOBILE, LATEST_BETAS
from .utils import ua_parse
from .version_compare import version_dict


# Simple email regex to keep people from submitting personal data.
EMAIL_RE = re.compile(r'[^\s]+@[^\s]+\.[^\s]{2,6}')

# Simple "possibly a URL" regex
URL_RE = re.compile(r'(://|www\.[^\s]|\.\w{2,}/)')


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
    matches = swearwords.find_swearwords(str)
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


def validate_no_email(str):
    """Disallow texts possibly containing emails addresses."""
    if EMAIL_RE.search(str):
        raise ValidationError(
            'Your feedback seems to contain an email address. Please remove '
            'this and similar personal data from the text, then try again. Thanks!')


def validate_no_urls(str):
    """Disallow text possibly containing a URL."""
    if URL_RE.search(str):
        raise ValidationError(
            'Your feedback seems to contain a URL. Please remove this and '
            'similar personal data from the text, then try again. Thanks!')
