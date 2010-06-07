from datetime import timedelta

from django import forms


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

class PeriodForm(forms.Form):
    period = forms.ChoiceField(choices=DASHBOARD_PERIODS)
