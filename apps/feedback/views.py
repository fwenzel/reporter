from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django import http
from django.views.decorators.vary import vary_on_headers

import jingo

from .forms import HappyForm, SadForm, validate_ua
from .models import Opinion


def enforce_user_agent(f):
    """
    View decorator enforcing feedback from the latest beta users only.

    Can be disabled with settings.ENFORCE_USER_AGENT = False.
    """
    def wrapped(request, *args, **kwargs):
        # Validate User-Agent request header.
        ua = request.META.get('HTTP_USER_AGENT', None)
        try:
            validate_ua(ua)
        except ValidationError:
            if request.method == 'GET':
                return http.HttpResponseRedirect(reverse('feedback.need_beta'))
            else:
                return http.HttpResponseBadRequest(
                    'User-Agent request header must be set.')

        # if we made it here, it's a latest beta user
        return f(request, ua=ua, *args, **kwargs)

    return wrapped


@vary_on_headers('User-Agent')
@enforce_user_agent
def give_feedback(request, ua, positive):
    """Feedback page (positive or negative)."""

    # Positive or negative feedback form?
    if positive:
        Formtype = HappyForm
        template = 'feedback/happy.html'
    else:
        Formtype = SadForm
        template = 'feedback/sad.html'

    if request.method == 'POST':
        form = Formtype(request.POST)
        if form.is_valid():
            # Remove URL if checkbox disabled.
            if not form.cleaned_data.get('add_url', False):
                form.cleaned_data['url'] = ''

            # Save to the DB.
            new_opinion = Opinion(
                positive=positive, url=form.cleaned_data.get('url', ''),
                description=form.cleaned_data['description'],
                user_agent=ua)
            new_opinion.save()

            return http.HttpResponseRedirect(reverse('feedback.thanks'))

    else:
        # URL is fed in by the feedback extension.
        url = request.GET.get('url', '')
        form = Formtype(initial={'url': url, 'add_url': False})

    return jingo.render(request, template, {'form': form})
