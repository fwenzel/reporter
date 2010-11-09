from datetime import timedelta

from collections import namedtuple

from django import forms
from django.forms import CharField, ChoiceField, BooleanField, HiddenInput, \
                         IntegerField
from django.utils.encoding import force_unicode

from tower import ugettext_lazy as _lazy

from product_details import product_details
from input.fields import SearchInput
from feedback import OSES, APPS, FIREFOX, MOBILE, LATEST_BETAS
from search.forms import SENTIMENT_CHOICES, SENTIMENTS, OS_CHOICES, \
                         PROD_CHOICES, VERSION_CHOICES


VERSION_CHOICES = VERSION_CHOICES.copy()
for app in APPS.values():
    VERSION_CHOICES[app] = VERSION_CHOICES[app][1:]


FieldDef = namedtuple("FieldDef", "default field keys")
def field_def(FieldType, default, widget=HiddenInput, choices=None):
    field_args = {"required": False, "label": "", "widget": widget}
    keys = None
    if choices is not None:
        field_args.update({"choices": choices})
        keys = set([key for key, value in choices])
    return FieldDef(default, FieldType(**field_args), keys)


FIELD_DEFS = {
    "q": field_def(
        CharField, "",
        widget=SearchInput(
            attrs={'placeholder': _lazy('Search for domain',
                                        'website_issues_search')}
        )
    ),
    "sentiment": field_def(ChoiceField, "", choices=SENTIMENT_CHOICES),
    "version": field_def(ChoiceField, VERSION_CHOICES[FIREFOX][0][0],
                         choices=VERSION_CHOICES[FIREFOX]),
    "product": field_def(ChoiceField, "firefox", choices=PROD_CHOICES),
    "os": field_def(ChoiceField, "", choices=OS_CHOICES),
    "show_one_offs": field_def(BooleanField, False),
    "page": field_def(IntegerField, 1),
    "site": field_def(IntegerField, None),
    "cluster": field_def(IntegerField, None)
}


class WebsiteIssuesSearchForm(forms.Form):

    # Fields that are submitted on text search:
    q = FIELD_DEFS['q'].field
    sentiment = FIELD_DEFS['sentiment'].field
    product = FIELD_DEFS['product'].field
    os = FIELD_DEFS['os'].field
    version = FIELD_DEFS['version'].field
    show_one_offs = FIELD_DEFS['show_one_offs'].field

    # These fields are reset on search:
    page = FIELD_DEFS['page'].field
    site = FIELD_DEFS['site'].field
    cluster = FIELD_DEFS['cluster'].field

    def clean(self):
        cleaned = super(WebsiteIssuesSearchForm, self).clean()

        for field_name, field_def in FIELD_DEFS.items():
            if BooleanField == type(field_def.field) \
                    and cleaned.get(field_name) not in (True, False):
                cleaned[field_name] = field_def.default
            if ChoiceField == type(field_def.field) \
                    and cleaned.get(field_name) not in field_def.keys:
                cleaned[field_name] = field_def.default

        if cleaned.get('product') and cleaned.get('os'):
            product = APPS[cleaned.get('product')]
            possible_oses = [os for os in OSES.values() if product in os.apps]
            if OSES[cleaned.get('os')] not in possible_oses:
                cleaned['os'] = FIELD_DEFS['os'].default

        if cleaned.get('page') is not None:
            cleaned['page'] = max(1, int(cleaned['page']))
        else:
            cleaned['page'] = FIELD_DEFS['page'].default

        return cleaned
