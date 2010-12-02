import datetime
import urlparse

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from annoying.decorators import autostrip
from tower import ugettext as _, ugettext_lazy as _lazy

from . import FIREFOX, MOBILE, LATEST_BETAS, OPINION_PRAISE, OPINION_ISSUE, OPINION_SUGGESTION, fields
from .models import Opinion
from .validators import (validate_swearwords, validate_no_html,
                         validate_no_email, validate_no_urls,
                         ExtendedURLValidator)
from .version_compare import version_int


class ExtendedURLField(forms.URLField):
    """(Forms) URL field allowing about: and chrome: URLs."""
    def __init__(self, *args, **kwargs):
        super(ExtendedURLField, self).__init__(*args, **kwargs)

        # Remove old URL validator, add ours instead.
        self.validators = filter(lambda x: not isinstance(x, URLValidator),
                                 self.validators)
        self.validators.append(ExtendedURLValidator())

    def to_python(self, value):
        """Do not convert about and chorme URLs to fake http addresses."""
        if value and not (value.startswith('about:') or
                          value.startswith('chrome://')):
            return super(ExtendedURLField, self).to_python(value)
        else:
            return value


class FeedbackForm(forms.Form):
    """Feedback form fields shared between feedback types."""

    add_url = forms.BooleanField(initial=True, required=False)
    # NB: The ID 'id_url' is hard-coded in the Testpilot extension to
    # accommodate pre-filling the field client-side.
    # Do not change unless you know what you are doing.
    url = ExtendedURLField(required=False, widget=forms.TextInput(
        attrs={'placeholder': 'http://', 'id': 'id_url'}))

    # NB the IDs 'id_manufacturer' and 'id_device' are hard-coded into the
    # Testpilot extension on Mobile.
    # Do not change unless you know what you are doing.
    manufacturer = forms.CharField(required=False, widget=forms.HiddenInput(
        attrs={'id': 'id_manufacturer'}))
    device = forms.CharField(required=False, widget=forms.HiddenInput(
        attrs={'id': 'id_device'}))

    def clean(self):
        # Ensure this is not a recent duplicate submission.
        if 'description' in self.cleaned_data:
            dupes = Opinion.objects.filter(
                description=self.cleaned_data['description'],
                created__gte=(datetime.datetime.now() -
                              datetime.timedelta(minutes=5)))[:1]
            if dupes:
                raise ValidationError(_('We already got your feedback! Thanks.'))

        return super(FeedbackForm, self).clean()

    def clean_url(self):
        """Sanitize URL input, remove PWs, etc."""
        url = self.cleaned_data['url']
        # Empty URLs are fine.
        if not url:
            return url

        # Do not mess with about: URLs (bug 600094).
        if self.cleaned_data['url'].startswith('about:'):
            return self.cleaned_data['url']

        # Note: http/https/chrome is already enforced by URL field type.
        parsed = urlparse.urlparse(url)

        # Rebuild URL to drop query strings, passwords, and the like.
        new_url = (parsed.scheme, parsed.hostname, parsed.path, None, None,
                   None)
        return urlparse.urlunparse(new_url)


@autostrip
class PraiseForm(FeedbackForm):
    """Form for Praise."""
    max_length=settings.MAX_FEEDBACK_LENGTH
    description = forms.CharField(widget=forms.Textarea(
        attrs={'placeholder': _lazy('Enter your feedback here.')}),
        max_length=max_length,
        validators=[validate_swearwords, validate_no_html,
                    validate_no_email, validate_no_urls])
    type = forms.CharField(initial=OPINION_PRAISE,
                                  widget=forms.HiddenInput(),
                                  required=True)

@autostrip
class IssueForm(FeedbackForm):
    """Form for negative feedback."""
    max_length=settings.MAX_FEEDBACK_LENGTH
    description = forms.CharField(widget=forms.Textarea(
        attrs={'placeholder': _lazy('Enter your feedback here.')}),
        max_length=max_length,
        validators=[validate_swearwords, validate_no_html,
                    validate_no_email, validate_no_urls])
    type = forms.CharField(initial=OPINION_ISSUE,
                                  widget=forms.HiddenInput(),
                                  required=True)


@autostrip
class SuggestionForm(FeedbackForm):
    """Form for submitting ideas and suggestions."""
    max_length=settings.MAX_SUGGESTION_LENGTH
    description = forms.CharField(widget=forms.Textarea(
        attrs={'placeholder': _lazy('Enter your suggestions here.')}),
        max_length=max_length,
        validators=[validate_swearwords, validate_no_html,
                    validate_no_email, validate_no_urls])
    type = forms.CharField(initial=OPINION_SUGGESTION,
                                  widget=forms.HiddenInput(),
                                  required=True)
