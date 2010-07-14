import re
import string

from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags

import product_details
from tower import ugettext as _

import swearwords

from . import FIREFOX, MOBILE, LATEST_BETAS
from .utils import ua_parse
from .version_compare import version_int


# Simple email regex to keep people from submitting personal data.
EMAIL_RE = re.compile(r'[^\s]+@[^\s]+\.[^\s]{2,6}')

# Simple "possibly a URL" regex
URL_RE = re.compile(r'(://|www\.[^\s]|\.\w{2,}/)')


def validate_ua(ua):
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


def validate_swearwords(str):
    """Soft swear word filter to encourage contructive feedback."""
    matches = swearwords.find_swearwords(str)
    if matches:
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
