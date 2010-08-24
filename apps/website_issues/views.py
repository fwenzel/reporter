from django.conf import settings
from django import http
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.shortcuts import get_object_or_404, get_list_or_404

import jingo

from input.decorators import cache_page
from feedback import LATEST_BETAS, FIREFOX
from feedback.models import Opinion

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

    full_url = '%s://%s' % (protocol, url_)
    sites, _ = _fetch_summaries(form, url=full_url)
    if sites:
        site = sites[0]
        clusters = site.all_clusters
    else:
        site = get_list_or_404(SiteSummary, url=full_url)[0]
        clusters = []

    # Fetch a pageful of clusters
    pager = Paginator(clusters, settings.SEARCH_PERPAGE)
    try:
        page = pager.page(form.cleaned_data['page'])
    except (EmptyPage, InvalidPage):
        page = pager.page(pager.num_pages)

    data = {"form": form,
            "page": page,
            "site": site,}
    return jingo.render(request, 'website_issues/website_issues.html', data)


@cache_page(use_get=True)
def site_theme(request, theme_id):
    """Display all comments in a per-site cluster."""
    cluster = get_object_or_404(Cluster, pk=theme_id)
    comments = cluster.secondary_comments

    # Paginate comments
    try:
        page_no = int(request.GET.get('page', '1'))
    except ValueError:
        page_no = 1
    pager = Paginator(comments, settings.SEARCH_PERPAGE)
    try:
        page = pager.page(page_no)
    except (EmptyPage, InvalidPage):
        page = pager.page(pager.num_pages)

    # Fetch full opinion list for this page
    opinions = Opinion.objects.filter(
        pk__in=(c.opinion_id for c in page.object_list))

    data = {"cluster": cluster,
            "page": page,
            "opinion_count": pager.count + 1,
            "opinions": opinions,
            "site": cluster.site_summary,}
    return jingo.render(request, 'website_issues/theme.html', data)
