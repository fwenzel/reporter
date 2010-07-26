from django.core.urlresolvers import reverse
from django.views.decorators.cache import cache_page
from django.conf import settings
from django import http
from .forms import WebsiteIssuesSearchForm
from django.db import connections, transaction
import jingo
from product_details import firefox_versions as versions

CONNECTION_NAME = "website_issues"

# MySQL really needs some hints on query execution: If the first two 
# sub-queries are grouped (like here), a query takes about 35ms. If not, 
# it takes about 20 seconds.    
SUMMARY_QUERY = u"""
    SELECT 
        `site_summary_id` as `site_id`, `site`.`url`, `site`.`s_size`, 
        `cluster_sentiment`, `cluster_id`, `cluster_size`, 
        `primary_description` as `cluster_text`
    FROM (
        SELECT * FROM (
            SELECT `url`, SUM(`site_size`) AS `s_size`
            FROM `website_issues_site_summary`
            WHERE (%(conditions)s) and `site_size` %(site_size_test)s
            GROUP BY `url`
            HAVING `s_size` %(site_size_test)s
            ORDER BY `s_size` DESC, `url` ASC
            LIMIT %(start)i, %(per_page)i
        ) AS `total`
        JOIN (
            SELECT `id`, `url` as `url_`
            FROM `website_issues_site_summary`
            WHERE (%(conditions)s) 
        ) AS `summary` ON `total`.url = `summary`.`url_`
    ) AS `site`
    STRAIGHT_JOIN (
         SELECT `site_summary_id`, `url`, `cluster_id`, 
                `cluster_size`, `primary_description`, 
                `positive` as `cluster_sentiment`
         FROM `website_issues_cluster_summary`
         WHERE (%(conditions)s)
    ) AS `cluster_summary` ON `site`.id = cluster_summary.site_summary_id
    ORDER BY `s_size` DESC, `url`, `cluster_summary`.`cluster_size` DESC"""

COUNT_QUERY = u"""
   SELECT COUNT(distinct `url`) 
   FROM `website_issues_site_summary`
   WHERE (%(conditions)s) and `site_size` %(site_size_test)s"""

# "order by id asc" implies "order by score desc"!
CLUSTER_CONTENTS_QUERY = u"""
    SELECT `description`
    FROM `website_issues_cluster`
    WHERE `cluster_id` = %(cluster_id)s AND cluster_id != id
    ORDER BY `id` ASC"""

def _fetch_summaries(form):
    if not form.is_valid(): return []    
    search_opts = form.cleaned_data
    cursor = connections[CONNECTION_NAME].cursor()
    
    # Condition values are interpolated by the database module.
    conditions = ["`version` = %(version)s"]
    parameters = {
       "version":  "<week>" if search_opts["search_type"] == "week"
                            else versions["LATEST_FIREFOX_DEVEL_VERSION"] }

    query = form.cleaned_data.get('q', '')
    if len(query):
        conditions.append("`url` LIKE CONCAT('%%',%(query)s,'%%')")
        parameters[ "query" ] = query
    
    site_size_test = "= 1" if search_opts["show_one_offs"] else "> 1"
    
    page = form.cleaned_data["page"]
    per_page = 50 if search_opts["show_one_offs"] else 10
    start = (page-1)*per_page
    summary_query = SUMMARY_QUERY % { 
        "start": start, 
        "per_page": per_page,
        "conditions": ") and (".join(conditions), 
        "site_size_test": site_size_test 
    }
    cursor.execute(summary_query, parameters)
    
    # may be None
    selected_sentiment = None
    if search_opts["sentiment"] == "happy": selected_sentiment = 1
    elif search_opts["sentiment"] == "sad": selected_sentiment = 0
    def filter_last_by_sentiment(sites):
        if selected_sentiment is None: return sites
        if len(sites) == 0: return sites
        if sites[-1]["sentiments"][selected_sentiment] > 0: return sites
        return sites[:-1]
    
    sites = []
    lasturl = None
    for row in cursor:
        site_id, url, size, sentiment, cluster_id, cluster_size, text = row
        if url != lasturl:
            sites = filter_last_by_sentiment(sites)
            sites.append( {"url": url, "size": size, "id": site_id,
                           "clusters": [], "sentiments": [0, 0]} )
            lasturl = url

        sites[-1][ "sentiments" ][sentiment] += cluster_size
        if selected_sentiment is None or sentiment == selected_sentiment:
            sites[-1][ "clusters" ].append( { "id": cluster_id,
                                              "primary": text,
                                              "cluster_size": cluster_size } )
    sites = filter_last_by_sentiment(sites)
    
    # Get count for pagination
    cursor = connections[CONNECTION_NAME].cursor()
    cursor.execute( COUNT_QUERY % { "conditions": ") and (".join(conditions), 
                                     "site_size_test": site_size_test },
                    parameters )
    count = cursor.fetchone()[0]
    return sites, FakePaginator(sites, per_page, count).page(page)


def _fetch_comments(cluster_id):
    cursor = connections[CONNECTION_NAME].cursor()
    cursor.execute(CLUSTER_CONTENTS_QUERY, {"cluster_id": cluster_id})
    return [ row[0] for row in cursor ]


class FakePaginator(object):
    class FakePage(object):
        def __init__(p, paginator, number, objects, start, stop): 
            p.has_next = lambda: paginator.count > stop
            p.has_previous = lambda: start > 1
            p.has_other_pages = lambda: p.has_next() or p.has_previous()
            p.next_page_number = lambda: number + 1
            p.previous_page_number = lambda: number - 1
            p.start_index = lambda: start
            p.end_index = lambda: stop
            p.object_list = objects
            p.number = number
            p.paginator = paginator

    def __init__(self, objects, pp, total):
        self.page = lambda n: FakePaginator.FakePage(self, n, objects,
                                       pp*(n-1) + 1, min(total, pp*n + 1))
        self.count = total
        self.num_pages = int(float(total-1) / pp)+1
        self.page_range = range(1, self.num_pages+1)


@cache_page(settings.CACHE_DEFAULT_PERIOD)
def website_issues(request):
    form = WebsiteIssuesSearchForm(request.GET)
    sites, page = _fetch_summaries(form)

    expanded_comments = []
    expanded_site_id = form.cleaned_data["site"]
    expanded_cluster_id = form.cleaned_data["cluster"]
    if expanded_cluster_id is not None:
        expanded_comments = _fetch_comments(expanded_cluster_id)
    
    def without_protocol(url):
        if url.find("://") == -1: return url
        return url[ url.find("://")+3 : ]

    def protocol(url):
        return url[ : url.find("://")+3 ]
    
    def search_url(fragment_id=None, **kwargs):
        return reverse("website_issues") + \
                "?" + form.search_parameters(**kwargs) + \
                ("" if fragment_id is None else "#" + fragment_id)
    
    response = { "form": form, 
                 "search_url": search_url,
                 "page": page,
                 "sites": sites, 
                 "without_protocol": without_protocol,
                 "protocol": protocol,
                 "expanded_cluster_id": expanded_cluster_id,
                 "expanded_site_id": expanded_site_id,
                 "expanded_comments": expanded_comments }
    return jingo.render(request, 
                        'website_issues/website_issues.html', 
                        response)

@cache_page(settings.CACHE_DEFAULT_PERIOD)
def cluster(request, cluster_id):
    response = { "expanded_comments": _fetch_comments(cluster_id) }
    return jingo.render(request, 'website_issues/comments.html', response)

