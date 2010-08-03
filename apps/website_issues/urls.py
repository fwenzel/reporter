from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('website_issues.views',
    url(r'^sites/?$',
        'website_issues', name='website_issues'),
    url(r'^sites/cluster/(?P<cluster_id>\d+)/?$',
         'cluster', name='website_issues_cluster')
)
