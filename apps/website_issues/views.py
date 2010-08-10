from django.conf import settings
from django import http
from django.core.paginator import Paginator, InvalidPage, EmptyPage

import jingo

from input.decorators import cache_page
from feedback import LATEST_BETAS, FIREFOX

from .forms import WebsiteIssuesSearchForm
from .models import Comment, Cluster, SiteSummary


def _fetch_summaries(form):
    if not form.is_valid(): return []
    search_opts = form.cleaned_data

    qs = SiteSummary.objects.all()

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

    if search_opts["show_one_offs"]:
        qs = qs.extra(where=['praise_count + issues_count = 1'])
    else:
        qs = qs.extra(where=['praise_count + issues_count > 1'])

    per_page = settings.SEARCH_PERPAGE
    if search_opts["show_one_offs"]:
        per_page *= 5
    pager = Paginator(qs, per_page)
    try:
        page = pager.page(search_opts["page"])
    except (EmptyPage, InvalidPage):
        page = pager.page(pager.num_pages)
    return page.object_list[:], page

def _fetch_comments(cluster_id):
    cluster = Cluster.objects.get(pk=cluster_id)
    qs = Comment.objects \
         .filter(cluster__id__exact=cluster_id) \
         .exclude(id__exact=cluster.primary_comment_id)
    return qs

@cache_page(use_get=True)
def website_issues(request):
    form = WebsiteIssuesSearchForm(request.GET)
    sites, page = _fetch_summaries(form)

    expanded_comments = []
    expanded_site_id = form.cleaned_data["site"]
    expanded_cluster_id = form.cleaned_data["cluster"]
    if expanded_cluster_id is not None:
        expanded_comments = _fetch_comments(expanded_cluster_id)

    response = {"form": form,
                "page": page,
                "sites": sites,
                "expanded_cluster_id": expanded_cluster_id,
                "expanded_site_id": expanded_site_id,
                "expanded_comments": expanded_comments}
    return jingo.render(request,
                        'website_issues/website_issues.html',
                        response)

@cache_page
def cluster(request, cluster_id):
    response = {"expanded_comments": _fetch_comments(cluster_id)}
    return jingo.render(request, 'website_issues/comments.html', response)
