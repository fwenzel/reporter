from django import template


register = template.Library()

@register.simple_tag
def smiley(style):
    """
    Renders a big smiley.
    style can be "sad" or "happy".
    """
    if not style in ('happy', 'sad'):
        return ''
    if style == 'happy': # positive smiley
        character = '&#9786;'
        title = 'happy face'
    else: # negative smiley
        character = '&#9785;'
        title = 'sad face'
    return '<span title="%s" class="smiley">%s</span>' % (title, character)
smiley.is_safe = True
