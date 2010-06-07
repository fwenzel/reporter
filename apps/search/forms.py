from datetime import date, timedelta

from django import forms
from haystack.forms import SearchForm
import product_details

from feedback import APPS, FIREFOX, OS_USAGE


PROD_CHOICES = (
    (FIREFOX.short, FIREFOX.pretty),
#    (MOBILE.short, MOBILE.pretty),
)
# TODO need this for Mobile as well
FIREFOX_BETA_VERSION_CHOICES = [
    (v[0], v[0]) for v in (sorted(
        product_details.firefox_history_development_releases.items(),
        key=lambda x: x[1], reverse=True))
]
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

        # Apply other filters verbatim
        for field in ('version', 'locale', 'os'):
            if self.cleaned_data[field]:
                filter = { field: self.cleaned_data[field] }
                sqs = sqs.filter(**filter)

        return sqs
