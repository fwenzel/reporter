from datetime import timedelta

from django import forms
from django.utils.encoding import force_unicode

from tower import ugettext_lazy as _lazy

import product_details
from input.fields import SearchInput
from search.forms import SENTIMENT_CHOICES, SENTIMENTS, LOCALE_CHOICES


SEARCH_TYPES = ('latest beta', 'week')
SEARCH_TYPE_CHOICES = zip(SEARCH_TYPES, SEARCH_TYPES)

DEFAULTS = {
   "q": "",
   "sentiment": '',
   "search_type": "week",
   "page": 1,
   "site": None,
   "cluster": None,
   "show_one_offs": False
}


class WebsiteIssuesSearchForm(forms.Form):

    # Fields that are submitted on text search:
    q = forms.CharField(
        required=False,
        label='',
        widget=SearchInput(
            attrs={'placeholder': _lazy('Search for domain',
                                        'website_issues_search')}
        ),
    )
    sentiment = forms.ChoiceField(
        required=False,
        choices=SENTIMENT_CHOICES,
        label='',
        widget=forms.HiddenInput
    )
    search_type = forms.ChoiceField(
        required=False,
        choices=SEARCH_TYPE_CHOICES,
        label='',
        widget=forms.HiddenInput
    )
    show_one_offs = forms.BooleanField(
        label='',
        required=False,
        widget=forms.HiddenInput
    )

    # These fields are reset on search:
    page = forms.IntegerField(widget=forms.HiddenInput, required=False)
    site = forms.IntegerField(widget=forms.HiddenInput, required=False)
    cluster = forms.IntegerField(widget=forms.HiddenInput, required=False)

    def clean(self):
        cleaned = super(WebsiteIssuesSearchForm, self).clean()

        if cleaned.get('sentiment') not in SENTIMENTS:
            cleaned['sentiment'] = DEFAULTS["sentiment"]

        if cleaned.get('search_type') not in SEARCH_TYPES:
            cleaned['search_type'] = DEFAULTS["search_type"]

        if cleaned.get('show_one_offs') not in (True, False):
            cleaned['show_one_offs'] = DEFAULTS["show_one_offs"]

        if cleaned['page'] is not None:
            cleaned['page'] = max(1, int(cleaned['page']))
        else:
            cleaned['page'] = DEFAULTS["page"]

        return cleaned
