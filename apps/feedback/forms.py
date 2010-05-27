from django import forms
from django.core.exceptions import ValidationError

from product_details import firefox_versions, mobile_details

from . import FIREFOX, MOBILE
from .utils import ua_parse
from .validators import validate_ua
from .version_compare import version_int


LATEST_BETAS = {
    FIREFOX: firefox_versions['LATEST_FIREFOX_DEVEL_VERSION'],
    MOBILE: mobile_details['beta_version'],
}


class FeedbackForm(forms.Form):
    """Feedback form fields shared between feedback types."""
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'Enter your feedback here.'}))
    ua = forms.CharField(widget=forms.HiddenInput(),
                         validators=[validate_ua])

class HappyForm(FeedbackForm):
    """Form for positive feedback."""
    positive = forms.BooleanField(initial=True,
                                  widget=forms.HiddenInput(),
                                  required=True)

class SadForm(FeedbackForm):
    """Form for negative feedback."""
    positive = forms.BooleanField(initial=False,
                                  widget=forms.HiddenInput(),
                                  required=False)
    add_url = forms.BooleanField(initial=True, required=False)
    url = forms.URLField(required=False, widget=forms.TextInput(
        attrs={'placeholder': 'http://'}))
