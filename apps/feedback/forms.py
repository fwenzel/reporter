import datetime
import urlparse

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from annoying.decorators import autostrip
from tower import ugettext as _, ugettext_lazy as _lazy

from input import RATING_USAGE, RATING_CHOICES
from feedback import (FIREFOX, MOBILE, LATEST_BETAS, OPINION_PRAISE,
                      OPINION_ISSUE, OPINION_SUGGESTION, OPINION_RATING,
                      OPINION_BROKEN, fields)
from feedback.models import Opinion
from feedback.validators import (validate_swearwords, validate_no_html,
                                 validate_no_email, validate_no_urls,
                                 ExtendedURLValidator)
from feedback.version_compare import version_int


# TODO: liberate
class ExtendedURLField(forms.URLField):
    """(Forms) URL field allowing about: and chrome: URLs."""
    def __init__(self, *args, **kwargs):
        super(ExtendedURLField, self).__init__(*args, **kwargs)

        # Remove old URL validator, add ours instead.
        self.validators = filter(lambda x: not isinstance(x, URLValidator),
                                 self.validators)
        self.validators.append(ExtendedURLValidator())

    def to_python(self, value):
        """Do not convert about and chrome URLs to fake http addresses."""
        if value and not (value.startswith('about:') or
                          value.startswith('chrome://')):
            return super(ExtendedURLField, self).to_python(value)
        else:
            return value

    def clean(self, url):
        """Sanitize URL input, remove PWs, etc."""
        # Run existing validators.
        url = super(ExtendedURLField, self).clean(url)

        # Empty URLs are fine.
        if not url:
            return url

        # Do not mess with about: URLs (bug 600094).
        if url.startswith('about:'):
            return url

        # Note: http/https/chrome is already enforced by URL field type.
        parsed = urlparse.urlparse(url)

        # Rebuild URL to drop query strings, passwords, and the like.
        new_url = (parsed.scheme, parsed.hostname, parsed.path, None, None,
                   None)
        return urlparse.urlunparse(new_url)


# TODO: liberate
class URLInput(forms.TextInput):
    """Text field with HTML5 URL Input type."""
    input_type = 'url'


class FeedbackForm(forms.Form):
    """Feedback form fields shared between feedback types."""

    add_url = forms.BooleanField(initial=True, required=False)
    # NB: The class 'url' is hard-coded in the Testpilot extension to
    # accommodate pre-filling the field client-side.
    # Do not change unless you know what you are doing.
    # TODO @deprecated id == id_url used to be used by the extension.
    url = ExtendedURLField(required=False, widget=forms.TextInput(
        attrs={'placeholder': 'http://', 'id': 'id_url',
               'class': 'url'}))

    # NB the classes 'manufacturer' and 'device' are hard-coded into the
    # Testpilot extension on Mobile.
    # Do not change unless you know what you are doing.
    # TODO @deprecated the id_* IDs used to be used by the extension.
    manufacturer = forms.CharField(required=False, widget=forms.HiddenInput(
        attrs={'id': 'id_manufacturer', 'class': 'manufacturer'}))
    device = forms.CharField(required=False, widget=forms.HiddenInput(
        attrs={'id': 'id_device', 'class': 'device'}))

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


@autostrip
class PraiseForm(FeedbackForm):
    """Form for praise."""
    max_length = settings.MAX_FEEDBACK_LENGTH
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
    max_length = settings.MAX_FEEDBACK_LENGTH
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
    max_length = settings.MAX_SUGGESTION_LENGTH
    description = forms.CharField(widget=forms.Textarea(
        attrs={'placeholder': _lazy('Enter your suggestions here.')}),
        max_length=max_length,
        validators=[validate_swearwords, validate_no_html,
                    validate_no_email, validate_no_urls])
    type = forms.CharField(initial=OPINION_SUGGESTION,
                           widget=forms.HiddenInput(),
                           required=True)


@autostrip
class RatingForm(forms.Form):
    """Form for rating-type feedback."""
    type = forms.CharField(initial=OPINION_RATING,
                           widget=forms.HiddenInput(),
                           required=True)

    def __init__(self, *args, **kwargs):
        super(RatingForm, self).__init__(*args, **kwargs)

        for question in RATING_USAGE:
            self.fields[question.short] = forms.TypedChoiceField(
                choices=RATING_CHOICES, coerce=lambda x: int(x),
                empty_value=None)


@autostrip
class BrokenWebsiteForm(FeedbackForm):
    """'Report Broken Website' form."""
    max_length = settings.MAX_FEEDBACK_LENGTH
    # NB: The class 'url' is hard-coded in the Testpilot extension to
    # accommodate pre-filling the field client-side.
    # Do not change unless you know what you are doing.
    url = ExtendedURLField(required=True, widget=URLInput(
        attrs={'placeholder': 'http://mozilla.org/broken', 'id': 'broken-url',
               'size': 45, 'class': 'url'}))
    description = forms.CharField(required=True, widget=forms.Textarea(
        attrs={'placeholder': _lazy('Example: Images were not loading, but '
                                    'the rest of the page was.'),
               'id': 'broken-desc', 'cols': 55, 'rows': 3,
               'class': 'countable'}),
        max_length=max_length,
        validators=[validate_swearwords, validate_no_html,
                    validate_no_email, validate_no_urls])
    type = forms.CharField(initial=OPINION_BROKEN,
                           widget=forms.HiddenInput(),
                           required=True)


@autostrip
class IdeaForm(SuggestionForm):
    """Flavor of SuggestionForm to be used for release feedback."""
    max_length = settings.MAX_SUGGESTION_LENGTH
    description = forms.CharField(widget=forms.Textarea(
        attrs={'placeholder': _lazy('Enter your suggestions here.'),
               'id': 'idea-desc', 'cols': 55, 'rows': 5,
               'class': 'countable'}),
        max_length=max_length,
        validators=[validate_swearwords, validate_no_html,
                    validate_no_email, validate_no_urls])
