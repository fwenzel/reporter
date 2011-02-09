from functools import wraps
import json

from django import http
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.views.decorators.cache import never_cache
from django.views.decorators.vary import vary_on_headers

import jingo
from tower import ugettext as _

import input
from input.decorators import cache_page, forward_mobile, negotiate
from input.urlresolvers import reverse
from feedback.forms import (PraiseForm, IssueForm, IdeaForm,
                            BrokenWebsiteForm, RatingForm, IdeaReleaseForm)
from feedback.models import Opinion, Rating
from feedback.utils import detect_language, ua_parse
from feedback.version_compare import Version


def enforce_ua(beta):
    """
    View decorator enforcing feedback from the right (latest beta, latest
    release) users only.

    Can be disabled with settings.ENFORCE_USER_AGENT = False.
    """
    def decorate(f):
        @wraps(f)
        def wrapped(request, *args, **kwargs):
            # Validate User-Agent request header.
            ua = request.META.get('HTTP_USER_AGENT', None)
            parsed = ua_parse(ua)

            if not parsed:  # Unknown UA.
                if request.method == 'GET':
                    return http.HttpResponseRedirect(reverse(
                        'feedback.download',
                        channel='beta' if beta else 'release'))
                else:
                    return http.HttpResponseBadRequest(
                        _('User-Agent request header must be set.'))

            if not settings.ENFORCE_USER_AGENT:
                return f(request, ua=ua, *args, **kwargs)

            this_ver = Version(parsed['version'])
            # Enforce beta releases.
            if beta:
                if this_ver.is_release:  # Forward release to release feedback.
                    return http.HttpResponseRedirect(
                        reverse('feedback', channel='release'))
                elif not this_ver.is_beta:  # Not a beta? Upgrade to beta.
                    return http.HttpResponseRedirect(
                            reverse('feedback.download', channel='beta'))

                # Check for outdated beta.
                ref_ver = Version(input.LATEST_BETAS[parsed['browser']])
                if this_ver < ref_ver:
                    return http.HttpResponseRedirect(
                            reverse('feedback.download', channel='beta'))

            # Enforce release versions.
            else:
                if this_ver.is_beta:  # Forward betas to beta feedback.
                    return http.HttpResponseRedirect(
                        reverse('feedback', channel='beta'))
                elif not this_ver.is_release:  # Not a release? Upgrade.
                    return http.HttpResponseRedirect(
                            reverse('feedback.download', channel='beta'))

                # Check for outdated release.
                ref_ver = Version(input.LATEST_RELEASE[parsed['browser']])
                if this_ver < ref_ver:
                    return http.HttpResponseRedirect(
                            reverse('feedback.download', channel='release'))

            # If we made it here, it's a valid version.
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
            input.OPINION_PRAISE.id: PraiseForm,
            input.OPINION_ISSUE.id: IssueForm,
            input.OPINION_IDEA.id: IdeaForm
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
    if type == input.OPINION_IDEA.id:
        div_id = 'ideaform'

    url_idea = request.GET.get('url', 'idea')
    data = {
        'form': form,
        'type': type,
        'div_id': div_id,
        'MAX_FEEDBACK_LENGTH': input.MAX_FEEDBACK_LENGTH,
        'url_idea': url_idea
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
def release_feedback(request, ua):
    """The index page for release version feedback."""
    data = {
        'RATING_USAGE': input.RATING_USAGE,
        'RATING_CHOICES': input.RATING_CHOICES,
    }

    if request.method == 'POST':
        try:
            type = int(request.POST.get('type'))
            FormType = {
                input.OPINION_RATING.id: RatingForm,
                input.OPINION_BROKEN.id: BrokenWebsiteForm,
                input.OPINION_IDEA.id: IdeaReleaseForm,
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
                    reverse('feedback', channel='release') + '#thanks')

        elif request.is_ajax():
            # For AJAX request, return errors only.
            return http.HttpResponseBadRequest(json.dumps(form.errors),
                                               mimetype='application/json')

        else:
            # For non-AJAX, return form with errors, and blank other feedback
            # forms.
            data.update(
                rating_form=(form if type == input.OPINION_RATING.id else
                             RatingForm()),
                website_form=(form if type == input.OPINION_BROKEN.id else
                              BrokenWebsiteForm()),
                idea_form=(form if type == input.OPINION_IDEA.id
                                 else IdeaReleaseForm()))

    else:
        data.update(rating_form=RatingForm(), website_form=BrokenWebsiteForm(),
                    idea_form=IdeaReleaseForm())

    template = 'feedback/%srelease_index.html' % (
        'mobile/' if request.mobile_site else '')
    return jingo.render(request, template, data)

feedback = negotiate(beta=beta_feedback, release=release_feedback)


@cache_page
def need_beta(request):
    """Encourage people to download a current beta version."""

    template = 'feedback/%sneed_beta.html' % (
        'mobile/' if request.mobile_site else '')
    return jingo.render(request, template)


@cache_page
def need_release(request):
    """Encourage people to download a current release version."""

    template = 'feedback/need_release.html'
    return jingo.render(request, template)

download = negotiate(release=need_release, beta=need_beta)


@cache_page
def thanks(request):
    """Thank you for your feedback."""

    template = 'feedback/%sthanks.html' % (
        'mobile/' if request.mobile_site else '')
    return jingo.render(request, template)


@cache_page
def opinion_detail(request, id):
    o = get_object_or_404(Opinion, pk=id)
    return jingo.render(request, 'feedback/opinion.html', {'opinion': o})


def save_opinion_from_form(request, type, ua, form):
    """Given a (valid) form and feedback type, save it to the DB."""
    locale = detect_language(request)

    # Remove URL if checkbox disabled or no URL submitted. Broken Website
    # report does not have the option to disable URL submission.
    if (type != input.OPINION_BROKEN.id and
        not (form.cleaned_data.get('add_url', False) and
             form.cleaned_data.get('url'))):
        form.cleaned_data['url'] = ''

    if type not in input.OPINION_TYPES:
        raise ValueError('Unknown type %s' % type)

    if type != input.OPINION_RATING.id:
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
        for question in input.RATING_USAGE:
            value = form.cleaned_data.get(question.short)
            if not value:
                continue
            Rating(opinion=opinion, type=question.id, value=value).save()
        return opinion
