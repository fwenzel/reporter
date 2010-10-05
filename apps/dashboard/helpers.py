import datetime

from django.conf import settings

from jingo import register
import jinja2


def new_context(context, **kw):
    """Helper adding variables to the existing context."""
    c = dict(context.items())
    c.update(kw)
    return c

def render_template(template, context):
    """Helper rendering a Jinja template."""
    t = register.env.get_template(template).render(context)
    return jinja2.Markup(t)


@register.function
@jinja2.contextfunction
def big_count_block(context, count):
    if not context['request'].mobile_site:
        tpl = 'dashboard/opinion_count.html'
    else:
        tpl = 'dashboard/mobile/opinion_count.html'
    return render_template(tpl, new_context(**locals()))


@register.function
@jinja2.contextfunction
def locales_block(context, locales, total, defaults=None):
    if not context['request'].mobile_site:
        tpl = 'dashboard/locales.html'
    else:
        tpl = 'dashboard/mobile/locales.html'
    return render_template(tpl, new_context(**locals()))


@register.inclusion_tag('dashboard/message_list.html')
@jinja2.contextfunction
def message_list(context, opinions, defaults=None, show_notfound=True):
    """A list of messages."""
    return new_context(**locals())


@register.function
@jinja2.contextfunction
def platforms_block(context, platforms, total, defaults=None):
    if not context['request'].mobile_site:
        tpl = 'dashboard/platforms.html'
    else:
        tpl = 'dashboard/mobile/platforms.html'
    return render_template(tpl, new_context(**locals()))


@register.function
@jinja2.contextfunction
def overview_block(context, sent, defaults=None):
    if not context['request'].mobile_site:
        tpl = 'dashboard/overview.html'
    else:
        tpl = 'dashboard/mobile/overview.html'
    return render_template(tpl, new_context(**locals()))


@register.function
@jinja2.contextfunction
def sites_block(context, sites, defaults=None):
    """Sidebar block for frequently mentioned sites."""
    if not (settings.DATABASES.get('website_issues') and sites):
        return None

    if not context['request'].mobile_site:
        tpl = 'dashboard/sites.html'
    else:
        tpl = 'dashboard/mobile/sites.html'
    return render_template(tpl, new_context(**locals()))


@register.function
@jinja2.contextfunction
def themes_block(context, themes, defaults=None):
    """Sidebar block for frequently used terms."""
    if not context['request'].mobile_site:
        tpl = 'dashboard/themes.html'
    else:
        tpl = 'dashboard/mobile/themes.html'
    return render_template(tpl, new_context(**locals()))


@register.inclusion_tag('dashboard/versions.html')
@jinja2.contextfunction
def versions_block(context, versions, defaults=None):
    return new_context(**locals())


@register.function
@jinja2.contextfunction
def when_block(context, form, defaults=None, selected=None):
    if not context['request'].mobile_site:
        tpl = 'dashboard/when.html'
    else:
        tpl = 'dashboard/mobile/when.html'
    return render_template(tpl, new_context(**locals()))


@register.function
def date_ago(**kwargs):
    """Returns the date for the given timedelta from now."""
    return datetime.date.today() - datetime.timedelta(**kwargs)


@register.inclusion_tag('includes/filter_box_toggle.html')
@jinja2.contextfunction
def filter_box_toggle(context, label=''):
    return new_context(**locals())


@register.inclusion_tag('dashboard/mobile/bar.html')
@jinja2.contextfunction
def mobile_bar(context, name, label, value=None, id=None, count=None, total=None,
               selected=False):
    """Filter / stats bars for mobile site."""
    if total:
        percentage = int(count / float(total) * 100)
    else:
        percentage = 100

    if not id:
        id = name

    return new_context(**locals())
