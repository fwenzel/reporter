from django.core.urlresolvers import reverse
from django import http

from annoying.decorators import render_to

from .forms import HappyForm, SadForm


@render_to()
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
