from datetime import date, timedelta

from django.conf import settings
from django import forms

from product_details import product_details
from product_details.version_compare import Version
from tower import ugettext_lazy as _lazy

from input import (FIREFOX, MOBILE, PLATFORM_USAGE, LATEST_VERSION, KNOWN_DEVICES,
                   KNOWN_MANUFACTURERS, get_channel)
from input.fields import DateInput, SearchInput


PROD_CHOICES = (
    (FIREFOX.short, FIREFOX.pretty),
    (MOBILE.short, MOBILE.pretty),
)

VERSION_CHOICES = {
    'beta': {
        FIREFOX: ([('--', _lazy('-- all --', 'version_choice'))] +
                  [(v, v) for v in FIREFOX.beta_versions]),
        MOBILE: ([('--', _lazy('-- all --', 'version_choice'))] +
                 [(v, v) for v in MOBILE.beta_versions]),
    },
    'release': {
        FIREFOX: ([('--', _lazy('-- all --', 'version_choice'))] +
                  [(v, v) for v in FIREFOX.release_versions]),
        MOBILE: ([('--', _lazy('-- all --', 'version_choice'))] +
                 [(v, v) for v in MOBILE.release_versions]),
    },
}

SENTIMENT_CHOICES = [('', _lazy('-- all --', 'sentiment_choice')),
    ('happy', _lazy('Praise')),
    ('sad', _lazy('Issues')),
    ('ideas', _lazy('Ideas')),
]
SENTIMENTS = ('happy', 'sad', 'ideas')

PLATFORM_CHOICES = ([('', _lazy('-- all --', 'platform_choice'))] +
              [(p.short, p.pretty) for p in PLATFORM_USAGE])

MANUFACTURER_CHOICES = [('Unknown', _lazy('Unknown'))] + [(m, m) for m in
                                                          KNOWN_MANUFACTURERS]

DEVICE_CHOICES = [('Unknown', _lazy('Unknown'))] + [(d, d) for d in
                                                    KNOWN_DEVICES]

LOCALE_CHOICES = [
    ('', _lazy('-- all --', 'locale_choice')),
    ('Unknown', _lazy('Unknown')),
] + [(lang, lang) for lang in sorted(product_details.languages)]


class ReporterSearchForm(forms.Form):
    q = forms.CharField(required=False, label='', widget=SearchInput(
        attrs={'placeholder': _lazy('Search by keyword')}))
    product = forms.ChoiceField(choices=PROD_CHOICES, label=_lazy('Product:'),
                                initial=FIREFOX.short, required=False)
    version = forms.ChoiceField(required=False, label=_lazy('Version:'),
            choices=VERSION_CHOICES[get_channel()][FIREFOX])
    sentiment = forms.ChoiceField(required=False, label=_lazy('Sentiment:'),
                                  choices=SENTIMENT_CHOICES)
    locale = forms.ChoiceField(required=False, label=_lazy('Locale:'),
                               choices=LOCALE_CHOICES)
    platform = forms.ChoiceField(required=False, label=_lazy('PLATFORM:'),
                           choices=PLATFORM_CHOICES)
    manufacturer = forms.ChoiceField(required=False,
                                     choices=MANUFACTURER_CHOICES)
    device = forms.ChoiceField(required=False, choices=DEVICE_CHOICES)
    date_start = forms.DateField(required=False, widget=DateInput(
        attrs={'class': 'datepicker'}), label=_lazy('Date range:'))
    date_end = forms.DateField(required=False, widget=DateInput(
        # L10n: This indicates the second part of a date range.
        attrs={'class': 'datepicker'}), label=_lazy('to'))
    page = forms.IntegerField(widget=forms.HiddenInput, required=False)

    # TODO(davedash): Make this prettier.
    def __init__(self, *args, **kwargs):
        """Pick version choices and initial product based on site ID."""
        super(ReporterSearchForm, self).__init__(*args, **kwargs)
        self.fields['version'].choices = (
                VERSION_CHOICES[get_channel()][FIREFOX])

        # Show Mobile versions if that was picked by the user.
        picked = None
        if self.is_bound:
            try:
                picked = self.fields['product'].clean(self.data.get('product'))
            except forms.ValidationError:
                pass
        if (picked == MOBILE.short or not self.is_bound and
            settings.SITE_ID == settings.MOBILE_SITE_ID):
            # We default to Firefox. Only change if this is the mobile site.
            self.fields['product'].initial = MOBILE.short
            self.fields['version'].choices = \
                    VERSION_CHOICES[get_channel()][MOBILE]

    def clean(self):
        cleaned = self.cleaned_data

        # Flip start and end if necessary.
        if (cleaned.get('date_start') and cleaned.get('date_end') and
            cleaned['date_start'] > cleaned['date_end']):
            (cleaned['date_start'], cleaned['date_end']) = (
                    cleaned['date_end'], cleaned['date_start'])

        # Ensure page is a natural number.
        try:
            cleaned['page'] = int(cleaned.get('page'))
            assert cleaned['page'] > 0
        except (TypeError, AssertionError):
            cleaned['page'] = 1

        if not cleaned.get('version'):
            cleaned['version'] = Version(LATEST_VERSION()[FIREFOX]).simplified
        elif cleaned['version'] == '--':
            cleaned['version'] = ''

        return cleaned
