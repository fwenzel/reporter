from datetime import date, timedelta

from django import forms
import product_details

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
SENTIMENTS = ('happy', 'sad')
SENTIMENT_CHOICES = [(s, s) for s in SENTIMENTS]
OS_CHOICES = [ (o.short, o.pretty) for o in OS_USAGE ]
try:
    LOCALE_CHOICES = [ (lang, lang) for lang in sorted(product_details.languages) ]
except AttributeError:
    # no product details?
    LOCALE_CHOICES = []


def add_empty(choices):
    """Adds an empty choice to a list of choices."""
    return [('', '-- all --')] + choices


class SearchInput(forms.TextInput):
    """HTML5 Search Input field."""
    input_type = 'search'


class ReporterSearchForm(forms.Form):
    q = forms.CharField(required=False, label='', widget=SearchInput(
        attrs={'placeholder': 'Search Terms'}))
    product = forms.ChoiceField(choices=PROD_CHOICES,
                                label='Product:')
    version = forms.ChoiceField(required=False,
        choices=add_empty(FIREFOX_BETA_VERSION_CHOICES),
        label='Version:')
    sentiment = forms.ChoiceField(required=False, label='Sentiment:',
                                  choices=add_empty(SENTIMENT_CHOICES))
    locale = forms.ChoiceField(required=False, label='Locale:',
                               choices=add_empty(LOCALE_CHOICES))
    os = forms.ChoiceField(required=False, label='OS:',
                           choices=add_empty(OS_CHOICES))
    date_start = forms.DateField(required=False, widget=forms.DateInput(
        attrs={'class': 'datepicker'}), label='Date range:')
    date_end = forms.DateField(required=False, widget=forms.DateInput(
        attrs={'class': 'datepicker'}), label='to')

    def clean(self):
        cleaned = super(ReporterSearchForm, self).clean()

        # Set "positive" value according to sentiment choice.
        if cleaned.get('sentiment', None) in SENTIMENTS:
            cleaned['positive'] = (cleaned['sentiment'] == 'happy')
        else:
            cleaned['positive'] = None

        # Sane default dates to avoid fetching huge amounts of data by default
        if not cleaned.get('date_end', None):
            cleaned['date_end'] = date.today()
        if not cleaned.get('date_start', None):
            cleaned['date_start'] = (cleaned['date_end'] - timedelta(days=30))
        return cleaned

    def clean_product(self):
        """Map product short names to id."""
        data = self.cleaned_data['product']
        return APPS[data].id

    def search(self):
        sqs = super(ReporterSearchForm, self).search()

        # Always restrict by date.
        date_end = self.cleaned_data['date_end'] + timedelta(days=1)
        sqs = sqs.filter(
            created__gte=self.cleaned_data['date_start']).filter(
            created__lt=date_end)

        # happy/sad
        if self.cleaned_data['positive'] is not None:
            sqs = sqs.filter(positive=self.cleaned_data['positive'])

        # Apply other filters verbatim
        for field in ('product', 'version', 'locale', 'os'):
            if self.cleaned_data[field]:
                filter = { field: self.cleaned_data[field] }
                sqs = sqs.filter(**filter)

        return sqs
