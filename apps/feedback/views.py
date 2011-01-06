from functools import wraps
import json

from django import http
from django.conf import settings
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.vary import vary_on_headers

import jingo
from tower import ugettext as _

from input import RATING_USAGE, RATING_CHOICES
from input.decorators import cache_page, forward_mobile
from input.urlresolvers import reverse

from feedback import (OPINION_PRAISE, OPINION_ISSUE, OPINION_SUGGESTION,
                      OPINION_RATING, OPINION_BROKEN, OPINION_TYPES)
from feedback.forms import (PraiseForm, IssueForm, SuggestionForm,
                            BrokenWebsiteForm, RatingForm, IdeaForm)
from feedback.models import Opinion, Rating
from feedback.utils import detect_language
from feedback.validators import validate_beta_ua, validate_stable_ua


def enforce_ua(beta):
    """
    View decorator enforcing feedback from the right (latest beta, latest
    stable) users only.

    Can be disabled with settings.ENFORCE_USER_AGENT = False.
    """
    validator = validate_beta_ua if beta else validate_stable_ua
    upgrade_url = 'feedback.need_beta' if beta else 'feedback.need_stable'

    def decorate(f):
        @wraps(f)
        def wrapped(request, *args, **kwargs):
            # Validate User-Agent request header.
            ua = request.META.get('HTTP_USER_AGENT', None)
            try:
                parsed = validator(ua)
            except ValidationError:
                if request.method == 'GET':
                    return http.HttpResponseRedirect(reverse(upgrade_url))
                else:
                    return http.HttpResponseBadRequest(
                        _('User-Agent request header must be set.'))

            # Forward beta users to beta channel
            if not beta and parsed and parsed.get('alpha'):
                return http.HttpResponseRedirect(
                    reverse('feedback.beta_feedback'))

            # if we made it here, it's a latest beta user
            return f(request, ua=ua, *args, **kwargs)

        return wrapped
    return decorate


@forward_mobile
@enforce_ua(beta=True)
@never_cache
def give_feedback(request, ua, type):
    """Submit feedback page."""

    try:
        FormType = {
            OPINION_PRAISE: PraiseForm,
            OPINION_ISSUE: IssueForm,
            OPINION_SUGGESTION: SuggestionForm
        }.get(type)
    except KeyError:
        return http.HttpResponseBadRequest(_('Invalid feedback type'))

    if request.method == 'POST':
        form = FormType(request.POST)
        if form.is_valid():
            # Save to the DB.
            save_opinion_from_form(request, type, ua, form)

            return http.HttpResponseRedirect(reverse('feedback.thanks'))

    else:
        # URL is fed in by the feedback extension.
        url = request.GET.get('url', '')
        form = FormType(initial={'url': url, 'add_url': False, 'type': type})

    # Set the div id for css styling
    div_id = 'feedbackform'
    if type == OPINION_SUGGESTION:
        div_id = 'suggestionform'

    url_suggestion = request.GET.get('url', 'suggestion')
    data = {
        'form': form,
        'type': type,
        'div_id': div_id,
        'MAX_FEEDBACK_LENGTH': settings.MAX_FEEDBACK_LENGTH,
        'OPINION_PRAISE': OPINION_PRAISE,
        'OPINION_ISSUE': OPINION_ISSUE,
        'OPINION_SUGGESTION': OPINION_SUGGESTION,
        'url_suggestion': url_suggestion
    }
    template = ('feedback/mobile/feedback.html' if request.mobile_site else
                'feedback/feedback.html')
    return jingo.render(request, template, data)


@forward_mobile
@vary_on_headers('User-Agent')
@enforce_ua(beta=True)
@cache_page
def beta_feedback(request, ua):
    """
    The index page for beta version feedback, which shows links to the happy
    and sad feedback pages.
    """
    template = 'feedback/%sbeta_index.html' % (
        'mobile/' if request.mobile_site else '')
    return jingo.render(request, template)


@forward_mobile
@vary_on_headers('User-Agent')
@enforce_ua(beta=False)
@cache_page
def stable_feedback(request, ua):
    """The index page for stable version feedback."""
    data = {
        'RATING_USAGE': RATING_USAGE,
        'RATING_CHOICES': RATING_CHOICES,
    }

    if request.method == 'POST':
        try:
            type = int(request.POST.get('type'))
            FormType = {
                OPINION_RATING: RatingForm,
                OPINION_BROKEN: BrokenWebsiteForm,
                OPINION_SUGGESTION: IdeaForm,
            }[type]
        except (ValueError, KeyError):
            return http.HttpResponseBadRequest(_('Invalid feedback type'))

        form = FormType(request.POST)
        if form.is_valid():
            save_opinion_from_form(request, type, ua, form)

            if request.is_ajax():
                return http.HttpResponse(json.dumps('ok'),
                                         mimetype='application/json')
            else:
                return http.HttpResponseRedirect(
                    reverse('feedback.stable_feedback') + '#thanks')

        elif request.is_ajax():
            # For AJAX request, return errors only.
            return http.HttpResponseBadRequest(json.dumps(form.errors),
                                               mimetype='application/json')

        else:
            # For non-AJAX, return form with errors, and blank other feedback
            # forms.
            data.update(
                rating_form=(form if type == OPINION_RATING else
                             RatingForm()),
                website_form=(form if type == OPINION_BROKEN else
                              BrokenWebsiteForm()),
                suggestion_form=(form if type == OPINION_SUGGESTION else
                                 IdeaForm()))

    else:
        data.update(rating_form=RatingForm(), website_form=BrokenWebsiteForm(),
                    suggestion_form=IdeaForm())

    template = 'feedback/stable_index.html'
    return jingo.render(request, template, data)


@cache_page
def need_beta(request):
    """Encourage people to download a current beta version."""

    template = 'feedback/%sneed_beta.html' % (
        'mobile/' if request.mobile_site else '')
    return jingo.render(request, template)


@cache_page
def need_stable(request):
    """Encourage people to download a current stable version."""

    template = 'feedback/need_stable.html'
    return jingo.render(request, template)


@cache_page
def thanks(request):
    """Thank you for your feedback."""

    template = 'feedback/%sthanks.html' % (
        'mobile/' if request.mobile_site else '')
    return jingo.render(request, template)


@cache_page
def opinion_detail(request, id):
    o = get_object_or_404(Opinion, pk=id)
    return jingo.render(request, 'feedback/opinion.html', {
        'opinion': o,
        'OPINION_PRAISE': OPINION_PRAISE,
        'OPINION_ISSUE': OPINION_ISSUE,
        'OPINION_SUGGESTION': OPINION_SUGGESTION})


def save_opinion_from_form(request, type, ua, form):
    """Given a (valid) form and feedback type, save it to the DB."""
    locale = detect_language(request)

    # Remove URL if checkbox disabled or no URL submitted. Broken Website
    # report does not have the option to disable URL submission.
    if (type != OPINION_BROKEN and
        not (form.cleaned_data.get('add_url', False) and
             form.cleaned_data.get('url'))):
        form.cleaned_data['url'] = ''

    if type not in OPINION_TYPES:
        raise ValueError('Unknown type %s' % type)

    if type != OPINION_RATING:
        return Opinion(
            type=type,
            url=form.cleaned_data.get('url', ''),
            description=form.cleaned_data['description'],
            user_agent=ua, locale=locale,
            manufacturer=form.cleaned_data['manufacturer'],
            device=form.cleaned_data['device']).save()

    else:
        opinion = Opinion(
            type=type,
            user_agent=ua, locale=locale)
        opinion.save()
        for question in RATING_USAGE:
            Rating(
                opinion=opinion,
                type=question.id,
                value=form.cleaned_data.get(question.short)).save()
        return opinion
