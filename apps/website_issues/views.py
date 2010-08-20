from django.conf import settings
from django import http
from django.core.paginator import Paginator, InvalidPage, EmptyPage

import jingo

from input.decorators import cache_page
from feedback import LATEST_BETAS, FIREFOX

from .forms import WebsiteIssuesSearchForm
from .models import Comment, Cluster, SiteSummary


def _fetch_summaries(form, url=None, count=None, one_offs=False):
    search_opts = form.cleaned_data

    qs = SiteSummary.objects.all()

    version = ("<week>" if search_opts["search_type"] == "week" else
               LATEST_BETAS[FIREFOX])
    qs = qs.filter(version__exact=version)

    # selected_sentiment = None means "both"
    selected_sentiment = None
    if search_opts["sentiment"] == "happy": selected_sentiment = 1
    elif search_opts["sentiment"] == "sad": selected_sentiment = 0
    qs = qs.filter(positive__exact=selected_sentiment)

    # If URL was specified, match it exactly, else fuzzy-search.
    if url:
        qs = qs.filter(url=url.lower())
    else:
        search_string = search_opts.get('q', '')
        if len(search_string):
            qs = qs.filter(url__contains=search_string.lower())

    if not url:
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


@cache_page(use_get=True)
def single_site(request, protocol, url_):
    """Display the clusters for a single site only."""
    form = WebsiteIssuesSearchForm(request.GET)
    if not form.is_valid():
        raise http.Http404

    sites, _ = _fetch_summaries(form, url='%s://%s' % (protocol, url_))
    if not sites:
        raise http.Http404
    site = sites[0]

    # Fetch a pageful of clusters
    clusters = site.all_clusters
    pager = Paginator(clusters, settings.SEARCH_PERPAGE)
    try:
        page = pager.page(form.cleaned_data['page'])
    except (EmptyPage, InvalidPage):
        page = pager.page(pager.num_pages)

    data = {"form": form,
            "page": page,
            "site": site,}
    return jingo.render(request, 'website_issues/website_issues.html', data)