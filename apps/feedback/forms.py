import datetime
import urlparse

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator

from annoying.decorators import autostrip
from tower import ugettext as _, ugettext_lazy as _lazy

from input import OPINION_PRAISE, OPINION_ISSUE, OPINION_IDEA
from feedback.models import Opinion
from feedback.validators import (validate_swearwords, validate_no_html,
                                 validate_no_email, validate_no_urls,
                                 ExtendedURLValidator)


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
        attrs={'placeholder': 'http://', 'class': 'url'}))

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
                raise ValidationError(
                        _('We already got your feedback! Thanks.'))

        return super(FeedbackForm, self).clean()


@autostrip
class PraiseForm(FeedbackForm):
    """Form for praise."""

    description = forms.CharField(
        widget=forms.Textarea(
            attrs={'data-max-length': OPINION_PRAISE.max_length}),
        label=_lazy('Please describe what you liked.'),
        max_length=OPINION_PRAISE.max_length,
        validators=[validate_swearwords, validate_no_html,
                    validate_no_email, validate_no_urls],
        required=True
        )
    type = forms.CharField(initial=OPINION_PRAISE.id,
                           widget=forms.HiddenInput(),
                           required=True)


@autostrip
class IssueForm(FeedbackForm):
    """Form for negative feedback."""
    description = forms.CharField(
        widget=forms.Textarea(
            attrs={'data-max-length': OPINION_ISSUE.max_length}),
        label=_lazy('Please describe your problem below.'),
        max_length=OPINION_ISSUE.max_length,
        validators=[validate_swearwords, validate_no_html,
                    validate_no_email, validate_no_urls],
        required=True
        )
    type = forms.CharField(initial=OPINION_ISSUE.id,
                           widget=forms.HiddenInput(),
                           required=True)


@autostrip
class IdeaForm(FeedbackForm):
    """Form for submitting ideas."""
    description = forms.CharField(
        widget=forms.Textarea(
            attrs={'data-max-length': OPINION_IDEA.max_length}),
        label=_lazy('Describe your idea below.'),
        max_length=OPINION_IDEA.max_length,
        validators=[validate_swearwords, validate_no_html,
                    validate_no_email, validate_no_urls],
        required=True
        )
    type = forms.CharField(initial=OPINION_IDEA.id,
                           widget=forms.HiddenInput(),
                           required=True)
