from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('website_issues.views',
    url(r'^sites/?$', 'website_issues', name='website_issues'),
    url(r'^site/(?P<url_>.+)$', 'single_site', name='single_site')
)
