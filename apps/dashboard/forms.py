from datetime import timedelta

from django import forms

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
LOCALE_CHOICES = [ (loc[0], loc[0]) for loc in product_details.languages ]
OS_CHOICES = [ (o.short, o.pretty) for o in OS_USAGE ]

DASHBOARD_PERIODS = (
    ('1d', '1 day'),
    ('1w', '1 week'),
    ('1m', '1 month'),
)
PERIOD_DELTAS = {
    '1d': timedelta(days=1),
    '1w': timedelta(weeks=1),
    '1m': timedelta(days=30),
}


class SearchForm(forms.Form):
    """Main search form."""
    q = forms.CharField()
    prod = forms.ChoiceField(choices=PROD_CHOICES)
    version = forms.ChoiceField(choices=FIREFOX_BETA_VERSION_CHOICES)
    locale = forms.ChoiceField(choices=LOCALE_CHOICES)
    os = forms.ChoiceField(choices=OS_CHOICES)
    date_from = forms.DateField()
    date_to = forms.DateField()


class PeriodForm(forms.Form):
    period = forms.ChoiceField(choices=DASHBOARD_PERIODS)
