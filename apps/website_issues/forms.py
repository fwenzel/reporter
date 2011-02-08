from collections import namedtuple

from django import forms
from django.forms import (CharField, ChoiceField, BooleanField, HiddenInput,
                          IntegerField)

from tower import ugettext_lazy as _lazy

from input import get_channel
from input.fields import SearchInput
from feedback import OSES, APPS, FIREFOX, MOBILE
from feedback.version_compare import simplify_version
from search.forms import (SENTIMENT_CHOICES, OS_CHOICES, PROD_CHOICES,
                          VERSION_CHOICES)


VERSION_CHOICES = {
    'beta': {
        FIREFOX: [(v, v) for v in FIREFOX.beta_versions],
        MOBILE: [(v, v) for v in MOBILE.beta_versions],
    },
    'release': {
        FIREFOX: [(v, v) for v in FIREFOX.release_versions],
        MOBILE: [(v, v) for v in MOBILE.release_versions],
    },
}

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
    "version": field_def(ChoiceField, 
                         VERSION_CHOICES[get_channel()][FIREFOX][0][0], 
                         choices=VERSION_CHOICES[get_channel()][FIREFOX]),
    "product": field_def(ChoiceField, FIREFOX.short, choices=PROD_CHOICES),
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

    # TODO(michaelk) This is similar, but not identical to what happens with
    #                themes and search. During refactoring we probably want to
    #                unify this somewhat.
    def __init__(self, *args, **kwargs):
        """Set available products/versions based on selected channel/product"""
        super(WebsiteIssuesSearchForm, self).__init__(*args, **kwargs)
        choices = VERSION_CHOICES[get_channel()]
        product_choices = \
            [(p.short, p.pretty) for p in (FIREFOX, MOBILE) if choices[p]]
        self.fields['product'].choices = product_choices
        FIELD_DEFS['product'] = field_def(ChoiceField, product_choices[0][0],
                                          choices=product_choices)
        product = self.data.get('product', FIREFOX)
        try: 
            if not choices[product]: product = FIREFOX
        except KeyError: 
            product = FIREFOX
        version_choices = choices[product]
        self.fields['version'].choices = version_choices
        self.fields['version'].initial = version_choices[0][0]
        FIELD_DEFS['version'] = field_def(ChoiceField, 
                                          version_choices[0][0], 
                                          choices=version_choices)
        self.cleaned_data = {}

    def clean(self):
        cleaned = super(WebsiteIssuesSearchForm, self).clean()

        for field_name, field_def in FIELD_DEFS.items():
            if field_name not in cleaned:
                cleaned[field_name] = field_def.default
                continue            
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

        if not cleaned.get('version'):
            product = cleaned.get('product', FIREFOX)
            cleaned['version'] = VERSION_CHOICES[get_channel()][product][0][0]

        if cleaned.get('page') is not None:
            cleaned['page'] = max(1, int(cleaned['page']))
        else:
            cleaned['page'] = FIELD_DEFS['page'].default

        return cleaned

    def full_clean(self):
        """Set cleaned data, with defaults for missing/invalid stuff."""
        super(WebsiteIssuesSearchForm, self).full_clean()
        try:
            return self.cleaned_data
        except AttributeError:
            self.cleaned_data = {}
            self.cleaned_data = self.clean()
            return self.cleaned_data
