from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django import http

from annoying.decorators import render_to

from .forms import HappyForm, SadForm, validate_ua


def enforce_user_agent(f):
    """
    View decorator enforcing feedback from the latest beta users only.

    Can be disabled with settings.ENFORCE_USER_AGENT = False.
    """
    def wrapped(request, *args, **kwargs):
        if request.method != 'GET' or not settings.ENFORCE_USER_AGENT:
            return f(request, *args, **kwargs)

        # validate user agent GET parameter
        ua = request.GET.get('ua', None)
        try:
            validate_ua(ua)
        except ValidationError:
            return http.HttpResponseRedirect(settings.URL_BETA)

        # if we made it here, it's a latest beta user
        return f(request, *args, **kwargs)

    return wrapped


@render_to()
@enforce_user_agent
def give_feedback(request, positive):
    """Feedback page (positive or negative)."""

    # positive or negative feedback form?
    if positive:
        Formtype = HappyForm
        data = {'TEMPLATE': 'feedback/happy.html'}
    else:
        Formtype = SadForm
        data = {'TEMPLATE': 'feedback/sad.html'}

    if request.method == 'POST':
        form = Formtype(request.POST)
        if form.is_valid():
            return http.HttpResponseRedirect(reverse('feedback.thanks'))

    else:
        # UA and URL are fed in by the feedback extension.
        ua = request.GET.get('ua', None)
        if not ua:
            return http.HttpResponseBadRequest(
                'User agent (ua) field is mandatory')

        url = request.GET.get('url', '')
        add_url = True if url else False
        form = Formtype(initial={'ua': ua, 'url': url, 'add_url': add_url})

    data['form'] = form
    return data
