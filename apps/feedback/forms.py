import datetime

from django import forms
from django.core.exceptions import ValidationError

from annoying.decorators import autostrip
from product_details import firefox_versions, mobile_details

from . import FIREFOX, MOBILE
from .models import Opinion
from .utils import ua_parse
from .validators import validate_ua, validate_swearwords, validate_no_html
from .version_compare import version_int


LATEST_BETAS = {
    FIREFOX: firefox_versions['LATEST_FIREFOX_DEVEL_VERSION'],
    MOBILE: mobile_details['beta_version'],
}


class FeedbackForm(forms.Form):
    """Feedback form fields shared between feedback types."""
    description = forms.CharField(widget=forms.TextInput(
        attrs={'placeholder': 'Enter your feedback here.'}),
        max_length=140, validators=[validate_swearwords, validate_no_html])

    def clean(self):
        # Ensure this is not a recent duplicate submission.
        if 'description' in self.cleaned_data:
            dupes = Opinion.objects.filter(
                description=self.cleaned_data['description'],
                created__gte=(datetime.datetime.now() -
                              datetime.timedelta(minutes=5)))[:1]
            if dupes:
                raise ValidationError('We already got your feedback! Thanks.')

        return super(FeedbackForm, self).clean()


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
    add_url = forms.BooleanField(initial=True, required=False)
    url = forms.URLField(required=False, widget=forms.TextInput(
        attrs={'placeholder': 'http://'}))
