"""Custom form fields."""

from django import forms


class DateInput(forms.DateInput):
    """HTML5 Date Input field."""
    input_type = 'date'

    def __init__(self, attrs=None, *args, **kwargs):
        default_attrs = {}
        if attrs:
            default_attrs.update(attrs)
        super(DateInput, self).__init__(default_attrs, *args, **kwargs)


class SearchInput(forms.TextInput):
    """HTML5 Search Input field."""
    input_type = 'search'
