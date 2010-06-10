from datetime import date, timedelta

from django import forms
from haystack.forms import SearchForm
import product_details

from feedback import APPS, FIREFOX, OS_USAGE
from feedback.validators import LATEST_BETAS
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
LOCALE_CHOICES = [ (lang, lang) for lang in sorted(product_details.languages) ]
OS_CHOICES = [ (o.short, o.pretty) for o in OS_USAGE ]


def add_empty(choices):
    """Adds an empty choice to a list of choices."""
    return [('', '-- all --')] + choices


class ReporterSearchForm(SearchForm):
    q = forms.CharField(label='Search issues:')
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
        attrs={'class': 'datepicker'}), label='From date:')
    date_end = forms.DateField(required=False, widget=forms.DateInput(
        attrs={'class': 'datepicker'}), label='Until date:')

    def search(self):
        sqs = super(ReporterSearchForm, self).search()

        # Sane default dates to avoid fetching huge amounts of data by default
        if not self.cleaned_data['date_end']:
            self.cleaned_data['date_end'] = date.today()
        if not self.cleaned_data['date_start']:
            self.cleaned_data['date_start'] = (self.cleaned_data['date_end'] -
                                               timedelta(days=30))
        sqs = sqs.filter(created__gte=self.cleaned_data['date_start']).filter(
            created__lte=self.cleaned_data['date_end'])

        if self.cleaned_data['product']:
            prod = self.cleaned_data['product']
            if prod in APPS:
                sqs = sqs.filter(product=APPS[prod].id)

        # happy/sad
        if self.cleaned_data['sentiment'] in SENTIMENTS:
            sqs = sqs.filter(
                positive=(self.cleaned_data['sentiment'] == 'happy'))

        # Apply other filters verbatim
        for field in ('version', 'locale', 'os'):
            if self.cleaned_data[field]:
                filter = { field: self.cleaned_data[field] }
                sqs = sqs.filter(**filter)

        return sqs
