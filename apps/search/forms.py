from datetime import date, timedelta

from django.conf import settings
from django import forms
from django.utils.functional import lazy

import product_details
from tower import ugettext_lazy as _lazy

from feedback import APPS, FIREFOX, MOBILE, OS_USAGE, LATEST_BETAS
from feedback.version_compare import simplify_version, version_int
from input.fields import DateInput, SearchInput
from input.utils import uniquifier


PROD_CHOICES = (
    (FIREFOX.short, FIREFOX.pretty),
    (MOBILE.short, MOBILE.pretty),
)
# TODO need this for Mobile as well
VERSION_CHOICES = {
    FIREFOX: [('', _lazy('-- all --', 'version_choice'))] + uniquifier(
        [(simplify_version(v[0]), v[0]) for v in
         sorted(product_details.firefox_history_development_releases.items(),
                key=lambda x: x[1], reverse=True) if
         version_int(v[0]) >= version_int(FIREFOX.hide_below)
        ], key=lambda x: x[0]),
    MOBILE: [
        ('', _lazy('-- all --', 'version_choice')),
        (simplify_version(LATEST_BETAS[MOBILE]), LATEST_BETAS[MOBILE]),
    ],
}

SENTIMENT_CHOICES = [
    ('', _lazy('-- all --', 'sentiment_choice')),
    ('happy', _lazy('Praise')),
    ('sad', _lazy('Issues')),
]
SENTIMENTS = ('happy', 'sad')


OS_CHOICES = ([('', _lazy('-- all --', 'os_choice'))] +
              [(o.short, o.pretty) for o in OS_USAGE])

LOCALE_CHOICES = [
    ('', _lazy('-- all --', 'locale_choice')),
    ('unknown', _lazy('unknown')),
] + [(lang, lang) for lang in sorted(product_details.languages)]


class ReporterSearchForm(forms.Form):
    q = forms.CharField(required=False, label='', widget=SearchInput(
        attrs={'placeholder': _lazy('Search by keyword')}))
    product = forms.ChoiceField(choices=PROD_CHOICES, label=_lazy('Product:'),
                                initial=FIREFOX.short)
    version = forms.ChoiceField(required=False, label=_lazy('Version:'),
                                choices=VERSION_CHOICES[FIREFOX])
    sentiment = forms.ChoiceField(required=False, label=_lazy('Sentiment:'),
                                  choices=SENTIMENT_CHOICES)
    locale = forms.ChoiceField(required=False, label=_lazy('Locale:'),
                               choices=LOCALE_CHOICES)
    os = forms.ChoiceField(required=False, label=_lazy('OS:'),
                           choices=OS_CHOICES)
    date_start = forms.DateField(required=False, widget=DateInput(
        attrs={'class': 'datepicker'}), label=_lazy('Date range:'))
    date_end = forms.DateField(required=False, widget=DateInput(
        # L10n: This indicates the second part of a date range.
        attrs={'class': 'datepicker'}), label=_lazy('to'))
    page = forms.IntegerField(widget=forms.HiddenInput, required=False)

    def __init__(self, *args, **kwargs):
        """Pick version choices and initial product based on site ID."""
        super(ReporterSearchForm, self).__init__(*args, **kwargs)

        # Show Mobile versions if that was picked by the user.
        picked = None
        if self.is_bound:
            try:
                picked = self.fields['product'].clean(self.data.get('product'))
            except forms.ValidationError:
                pass
        if (picked == MOBILE.short or not self.is_bound and
            settings.SITE_ID == settings.MOBILE_SITE_ID):
            print picked
            # We default to Firefox. Only change if this is the mobile site.
            self.fields['product'].initial = MOBILE.short
            self.fields['version'].choices = VERSION_CHOICES[MOBILE]

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
