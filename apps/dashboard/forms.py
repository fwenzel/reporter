from datetime import timedelta

from django import forms

from tower import ugettext_lazy as _


DASHBOARD_PERIODS = (
    ('1d', _(u'1 day')),
    ('1w', _(u'1 week')),
    ('1m', _(u'1 month')),
    ('all', _(u'all')),
)
PERIOD_DELTAS = {
    '1d': timedelta(days=1),
    '1w': timedelta(weeks=1),
    '1m': timedelta(days=30),
}

class PeriodForm(forms.Form):
    period = forms.ChoiceField(choices=DASHBOARD_PERIODS)
