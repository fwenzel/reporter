from django.conf import settings
from django import http
from django.core.paginator import Paginator, InvalidPage, EmptyPage

import jingo

from input.decorators import cache_page
from feedback import LATEST_BETAS, FIREFOX

from .forms import WebsiteIssuesSearchForm
from .models import Comment, Cluster, SiteSummary


def _fetch_summaries(form, count=None, one_offs=False):
    search_opts = form.cleaned_data

    qs = SiteSummary.objects.all()

    if search_opts['site']:
        qs = qs.filter(pk=search_opts['site'])

    version = "<week>" if search_opts["search_type"] == "week" \
                       else LATEST_BETAS[FIREFOX]
    qs = qs.filter(version__exact=version)

    # selected_sentiment = None means "both"
    selected_sentiment = None
    if search_opts["sentiment"] == "happy": selected_sentiment = 1
    elif search_opts["sentiment"] == "sad": selected_sentiment = 0
    qs = qs.filter(positive__exact=selected_sentiment)

    search_string = search_opts.get('q', '')
    if len(search_string):
        qs = qs.filter(url__contains=search_string.lower())

    if not search_opts['site']:
        if one_offs or search_opts["show_one_offs"]:
            qs = qs.extra(where=['praise_count + issues_count = 1'])
        else:
            qs = qs.extra(where=['praise_count + issues_count > 1'])

    if count:
        per_page = count
    else:
        per_page = settings.SEARCH_PERPAGE
        if search_opts["show_one_offs"]:
            per_page *= 5
    pager = Paginator(qs, per_page)
    try:
        page = pager.page(search_opts["page"])
    except (EmptyPage, InvalidPage):
        page = pager.page(pager.num_pages)
    return page.object_list[:], page


@cache_page(use_get=True)
def website_issues(request):
    form = WebsiteIssuesSearchForm(request.GET)
    sites = page = one_offs = None
    if not form.is_valid():
        raise http.Http404
    else:
        if form.cleaned_data['site']:
            # Display single site
            return _site_themes(request, form)

        sites, page = _fetch_summaries(form)
        # Grab one-off domains for sidebar.
        if not (form.cleaned_data['show_one_offs'] or
                form.cleaned_data['site']):
            one_offs, _ = _fetch_summaries(form, count=settings.TRENDS_COUNT,
                                           one_offs=True)

    data = {"form": form,
            "page": page,
            "sites": sites,
            "one_offs": one_offs,}
    return jingo.render(request, 'website_issues/website_issues.html', data)


def _site_themes(request, form):
    """Display the clusters for a single site only."""
    sites, _ = _fetch_summaries(form)
    if not sites:
        raise http.Http404
    site = sites[0]

    # Fetch a pagefull of clusters
    clusters = site.all_clusters
    pager = Paginator(clusters, settings.SEARCH_PERPAGE)
    try:
        page = pager.page(form.cleaned_data['page'])
    except (EmptyPage, InvalidPage):
        page = pager.page(pager.num_pages)

    data = {"form": form,
            "page": page,
            "site_id": form.cleaned_data['site'],
            "site": site,}
    return jingo.render(request, 'website_issues/website_issues.html', data)


@cache_page
def cluster(request, cluster_id):
    cluster = Cluster.objects.get(cluster_id)
    response = {"expanded_comments": cluster.secondary_comments}
    return jingo.render(request, 'website_issues/comments.html', response)
