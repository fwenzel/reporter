import datetime

from jingo import register
import jinja2


def new_context(context, **kw):
    """Helper adding variables to the existing context."""
    c = dict(context.items())
    c.update(kw)
    return c


@register.inclusion_tag('dashboard/opinion_count.html')
def big_count_block(count):
    return locals()


@register.inclusion_tag('dashboard/locales.html')
@jinja2.contextfunction
def locales_block(context, locales, total, defaults=None):
    return new_context(**locals())


@register.inclusion_tag('dashboard/message_list.html')
@jinja2.contextfunction
def message_list(context, opinions, defaults=None, show_notfound=True):
    """A list of messages."""
    return new_context(**locals())


@register.inclusion_tag('dashboard/platforms.html')
@jinja2.contextfunction
def platforms_block(context, platforms, total, defaults=None):
    return new_context(**locals())


@register.inclusion_tag('dashboard/overview.html')
@jinja2.contextfunction
def overview_block(context, sent, defaults=None):
    return new_context(**locals())


@register.inclusion_tag('dashboard/sites.html')
@jinja2.contextfunction
def sites_block(context, sites, defaults=None):
    """Sidebar block for frequently mentioned sites."""
    return new_context(**locals())


@register.inclusion_tag('dashboard/themes.html')
@jinja2.contextfunction
def themes_block(context, themes, defaults=None):
    """Sidebar block for frequently used terms."""
    return new_context(**locals())


@register.inclusion_tag('dashboard/versions.html')
@jinja2.contextfunction
def versions_block(context, versions, defaults=None):
    return new_context(**locals())


@register.inclusion_tag('dashboard/when.html')
@jinja2.contextfunction
def when_block(context, form, defaults=None, selected=None):
    return new_context(**locals())


@register.function
def date_ago(**kwargs):
    """Returns the date for the given timedelta from now."""
    return datetime.date.today() - datetime.timedelta(**kwargs)


@register.inclusion_tag('includes/filter_box_toggle.html')
@jinja2.contextfunction
def filter_box_toggle(context, label=''):
    return new_context(**locals())
