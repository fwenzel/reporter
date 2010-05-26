from django import forms


class FeedbackForm(forms.Form):
    """Feedback form fields shared between feedback types."""
    description = forms.CharField(
        widget=forms.Textarea(attrs={
            'placeholder': 'Enter your feedback here.'}))
    ua = forms.CharField(widget=forms.HiddenInput())

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
