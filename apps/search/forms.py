from datetime import date, timedelta

from django import forms

from haystack.forms import SearchForm


class ReporterSearchForm(SearchForm):
    date_start = forms.DateField(required=False, widget=forms.DateInput(
        attrs={'class': 'datepicker'}))
    date_end = forms.DateField(required=False, widget=forms.DateInput(
        attrs={'class': 'datepicker'}))

    def search(self):
        sqs = super(ReporterSearchForm, self).search()

        # Sane default values to avoid fetching huge amounts of data by default
        if not self.cleaned_data['date_end']:
            self.cleaned_data['date_end'] = date.today()
        if not self.cleaned_data['date_start']:
            self.cleaned_data['date_start'] = self.cleaned_data['date_end'] - timedelta(days=30)

        sqs = sqs.filter(created__gte=self.cleaned_data['date_start']).filter(
            created__lte=self.cleaned_data['date_end'])

        return sqs
