from datetime import date, timedelta

from django import forms
from haystack.forms import SearchForm
import product_details

from feedback import FIREFOX, OS_USAGE


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


class DBSearchForm(forms.Form):
    """Main search form."""
    q = forms.CharField()
    prod = forms.ChoiceField(choices=PROD_CHOICES)
    version = forms.ChoiceField(choices=FIREFOX_BETA_VERSION_CHOICES)
    locale = forms.ChoiceField(choices=LOCALE_CHOICES)
    os = forms.ChoiceField(choices=OS_CHOICES)
    date_from = forms.DateField()
    date_to = forms.DateField()


class ReporterSearchForm(SearchForm):
    q = forms.CharField(label='Search issues')
    locale = forms.ChoiceField(required=False,
                               choices=add_empty(LOCALE_CHOICES))
    os = forms.ChoiceField(required=False, label='OS',
                           choices=add_empty(OS_CHOICES))
    date_start = forms.DateField(required=False, widget=forms.DateInput(
        attrs={'class': 'datepicker'}), label='From date')
    date_end = forms.DateField(required=False, widget=forms.DateInput(
        attrs={'class': 'datepicker'}), label='Until date')

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

        if self.cleaned_data['locale']:
            sqs = sqs.filter(locale=self.cleaned_data['locale'])

        if self.cleaned_data['os']:
            sqs = sqs.filter(os=self.cleaned_data['os'])

        return sqs
