from datetime import date, timedelta

from django import forms
import product_details
from tower import ugettext_lazy as _lazy

from feedback import APPS, FIREFOX, OS_USAGE, LATEST_BETAS
from feedback.version_compare import simplify_version


PROD_CHOICES = (
    (FIREFOX.short, FIREFOX.pretty),
#    (MOBILE.short, MOBILE.pretty),
)
# TODO need this for Mobile as well
FIREFOX_BETA_VERSION_CHOICES = [
    (simplify_version(LATEST_BETAS[FIREFOX]),
     LATEST_BETAS[FIREFOX])
]
SENTIMENT_CHOICES = [
    ('happy', _lazy('happy')),
    ('sad', _lazy('sad')),
]
SENTIMENTS = ('happy', 'sad')
OS_CHOICES = [ (o.short, o.pretty) for o in OS_USAGE ]
try:
    LOCALE_CHOICES = [ ('unknown', _lazy('unknown')) ] + [
        (lang, lang) for lang in sorted(product_details.languages) ]
except AttributeError:
    # no product details?
    LOCALE_CHOICES = []


def add_empty(choices):
    """Adds an empty choice to a list of choices."""
    # L10n: This is a placeholder in the search form, for all items in a list.
    return [('', _lazy('-- all --'))] + choices


class SearchInput(forms.TextInput):
    """HTML5 Search Input field."""
    input_type = 'search'


class ReporterSearchForm(forms.Form):
    q = forms.CharField(required=False, label='', widget=SearchInput(
        attrs={'placeholder': _lazy('Search Terms')}))
    product = forms.ChoiceField(choices=PROD_CHOICES,
                                label=_lazy('Product:'))
    version = forms.ChoiceField(required=False,
        choices=add_empty(FIREFOX_BETA_VERSION_CHOICES),
        label=_lazy('Version:'))
    sentiment = forms.ChoiceField(required=False, label=_lazy('Sentiment:'),
                                  choices=add_empty(SENTIMENT_CHOICES))
    locale = forms.ChoiceField(required=False, label=_lazy('Locale:'),
                               choices=add_empty(LOCALE_CHOICES))
    os = forms.ChoiceField(required=False, label=_lazy('OS:'),
                           choices=add_empty(OS_CHOICES))
    date_start = forms.DateField(required=False, widget=forms.DateInput(
        attrs={'class': 'datepicker'}), label=_lazy('Date range:'))
    date_end = forms.DateField(required=False, widget=forms.DateInput(
        # L10n: This indicates the second part of a date range.
        attrs={'class': 'datepicker'}), label=_lazy('to'))

    page = forms.IntegerField(widget=forms.HiddenInput, required=False)

    def clean(self):
        cleaned = super(ReporterSearchForm, self).clean()

        # Set "positive" value according to sentiment choice.
        if cleaned.get('sentiment') in SENTIMENTS:
            cleaned['positive'] = (cleaned['sentiment'] == 'happy')
        else:
            cleaned['positive'] = None

        # Sane default dates to avoid fetching huge amounts of data by default
        if not cleaned.get('date_end'):
            cleaned['date_end'] = date.today()
        if not cleaned.get('date_start'):
            cleaned['date_start'] = (cleaned['date_end'] - timedelta(days=30))

        if not cleaned.get('page'):
            cleaned['page'] = 1

        return cleaned

    def clean_product(self):
        """Map product short names to id."""
        data = self.cleaned_data['product']
        return APPS[data].id
