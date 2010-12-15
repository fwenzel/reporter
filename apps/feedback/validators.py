import re
import string

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core import validators
from django.utils.html import strip_tags

from product_details import product_details
from tower import ugettext as _

import swearwords

from feedback import FIREFOX, MOBILE, LATEST_BETAS, LATEST_STABLE
from feedback.utils import ua_parse
from feedback.version_compare import version_int, version_dict


# Simple email regex to keep people from submitting personal data.
EMAIL_RE = re.compile(r'[^\s]+@[^\s]+\.[^\s]{2,6}')

# Simple "possibly a URL" regex
URL_RE = re.compile(r'(://|www\.[^\s]|\.\w{2,}/)')


def validate_beta_ua(ua):
    """Ensure a UA string represents a valid latest beta version."""
    parsed = ua_parse(ua)
    if not parsed:
        raise ValidationError(_('User agent string was not recognizable.'))

    # compare to latest beta, if UA enforced.
    if settings.ENFORCE_USER_AGENT:
        ref_version = version_int(LATEST_BETAS[parsed['browser']])
        this_version = version_int(parsed['version'])

        if ref_version > this_version:
            raise ValidationError(_('Submitted User Agent is not the '
                                    'latest beta version.'))


def validate_stable_ua(ua):
    """Ensure a UA string represents a valid latest stable version."""
    parsed = ua_parse(ua)
    if not parsed:
        raise ValidationError(_('User agent string was not recognizable.'))

    # compare to latest beta, if UA enforced.
    if settings.ENFORCE_USER_AGENT:
        ref_version = version_dict(LATEST_STABLE[parsed['browser']])
        this_version = version_dict(parsed['version'])

        if ((ref_version['major'], ref_version['minor1']) >
            (this_version['major'], this_version['minor1'])):
            raise ValidationError(_('Submitted User Agent is not the '
                                    'latest stable version.'))
        return this_version


def validate_swearwords(str):
    """Soft swear word filter to encourage contructive feedback."""
    matches = swearwords.find_swearwords(str)
    if matches:
        # L10n: "Swear words" are cuss words/offensive words.
        raise ValidationError(
            _('Your comment contains swear words (%s). In order to help us '
              'improve our products, please use words that help us create an '
              'action or to-do from your constructive feedback. Thanks!') % (
                ', '.join(matches)))


def validate_no_html(str):
    """Disallow HTML."""
    if strip_tags(str) != str:
        raise ValidationError(_('Feedback must not contain HTML.'))


def validate_no_email(str):
    """Disallow texts possibly containing emails addresses."""
    if EMAIL_RE.search(str):
        raise ValidationError(
            _('Your feedback seems to contain an email address. Please remove '
              'this and similar personal data from the text, then try again. '
              'Thanks!'))


def validate_no_urls(str):
    """Disallow text possibly containing a URL."""
    if URL_RE.search(str):
        raise ValidationError(
            _('Your feedback seems to contain a URL. Please remove this and '
              'similar personal data from the text, then try again. Thanks!'))


class ExtendedURLValidator(validators.URLValidator):
    """URL validator that allows about: and chrome: URLs."""
    regex = re.compile(
        r'^about:[a-z]+$|'  # about:something URLs
        r'^chrome://[a-z][/?\.\S]+$|'  # chrome://... URLs
        r'^https?://' # http:// or https://
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|' # domain...
        r'localhost|' # localhost...
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})' # ...or ip
        r'(?::\d+)?' # optional port
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)
