import datetime
import urlparse

from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from annoying.decorators import autostrip
from product_details import firefox_versions, mobile_details
from tower import ugettext as _, ugettext_lazy as _lazy

from . import FIREFOX, MOBILE, LATEST_BETAS
from .models import Opinion
from .validators import (validate_swearwords, validate_no_html,
                         validate_no_email, validate_no_urls)
from .version_compare import version_int


class FeedbackForm(forms.Form):
    """Feedback form fields shared between feedback types."""
    description = forms.CharField(widget=forms.TextInput(
        attrs={'placeholder': _lazy('Enter your feedback here.')}),
        max_length=settings.MAX_FEEDBACK_LENGTH,
        validators=[validate_swearwords, validate_no_html,
                    validate_no_email, validate_no_urls])

    add_url = forms.BooleanField(initial=True, required=False)

    # NB: The ID 'id_url' is hard-coded in the Testpilot extension to
    # accommodate pre-filling the field client-side.
    # Do not change unless you know what you are doing.
    url = forms.URLField(required=False, widget=forms.TextInput(
        attrs={'placeholder': 'http://', 'id': 'id_url'}))

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
        parsed = urlparse.urlparse(url)

        # Note: http/https is already enforced by URL field type.

        # Rebuild URL to drop query strings, passwords, and the like.
        new_url = (parsed.scheme, parsed.hostname, parsed.path, None, None,
                   None)
        return urlparse.urlunparse(new_url)


@autostrip
class HappyForm(FeedbackForm):
    """Form for positive feedback."""
    positive = forms.BooleanField(initial=True,
                                  widget=forms.HiddenInput(),
                                  required=True)

@autostrip
class SadForm(FeedbackForm):
    """Form for negative feedback."""
    positive = forms.BooleanField(initial=False,
                                  widget=forms.HiddenInput(),
                                  required=False)
