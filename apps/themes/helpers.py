import jinja2
from jingo import register

from feedback import OPINION_PRAISE, OPINION_SUGGESTION


@register.filter
def is_praise(opinion):
    return opinion.type == OPINION_PRAISE


@register.filter
def is_suggestion(opinion):
    return opinion.type == OPINION_SUGGESTION


def new_context(context, **kw):
    """Helper adding variables to the existing context."""
    c = dict(context.items())
    c.update(kw)
    return c


@register.inclusion_tag('themes/theme_list.html')
@jinja2.contextfunction
def theme_list(context, themes):
    """A list of messages."""
    return new_context(**locals())


@register.inclusion_tag('themes/filter_list.html')
def filter_list(filters):
    """A list of messages."""
    return locals()
