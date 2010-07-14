from datetime import timedelta

from django import forms

from tower import ugettext_lazy as _lazy


DASHBOARD_PERIODS = (
    ('1d', _lazy('1 day')),
    ('1w', _lazy('1 week')),
    ('1m', _lazy('1 month')),
    ('all', _lazy('all')),
)
PERIOD_DELTAS = {
    '1d': timedelta(days=1),
    '1w': timedelta(weeks=1),
    '1m': timedelta(days=30),
}

class PeriodForm(forms.Form):
    period = forms.ChoiceField(choices=DASHBOARD_PERIODS)
