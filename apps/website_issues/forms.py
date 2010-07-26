from datetime import timedelta
from django import forms
from django.utils.encoding import force_unicode
from tower import ugettext_lazy as _lazy
from input.fields import SearchInput
import product_details
import urllib

from search.forms import SENTIMENT_CHOICES, SENTIMENTS
from search.forms import LOCALE_CHOICES

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
        widget=SearchInput(attrs={'placeholder': _lazy('Filter by Site',
                                                'website_issues_search')}),
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

    def search_parameters(self, **kwargs):
        """Return the current form values as parameters for a new query,
           optionally overriding them. Used to modify the page without
           losing search context."""
        parameters = self.cleaned_data.copy()
        # page is reset on every change of search
        del parameters['page']
        for name in parameters.keys()[:]:
            if parameters[name] == DEFAULTS[name]:
                del parameters[name]
        for name, value in kwargs.iteritems():
            parameters[ name ] = value
        return urllib.urlencode(parameters)

    def clean(self):
        cleaned = super(WebsiteIssuesSearchForm, self).clean()

        if cleaned.get('sentiment') not in SENTIMENTS:
            cleaned['sentiment'] = DEFAULTS["sentiment"]
        
        if cleaned.get('search_type') not in SEARCH_TYPES:
            cleaned['search_type'] = DEFAULTS["search_type"]

        if cleaned.get('show_one_offs') not in (True, False):
            cleaned['show_one_offs'] = DEFAULTS["show_one_offs"]

        if cleaned.get('page'):
            cleaned['page'] = max(1, int(cleaned['page']))
        else:
            cleaned['page'] = DEFAULTS["page"]
        
        if not cleaned.get('site'):
            cleaned['site'] = DEFAULTS["site"]

        if not cleaned.get('cluster'):
            cleaned['cluster'] = DEFAULTS["cluster"]

        return cleaned
