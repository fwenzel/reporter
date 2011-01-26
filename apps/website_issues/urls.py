from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('website_issues.views',
    url(r'^sites/?$', 'website_issues', name='website_issues'),
    url(r'^site/(?P<protocol>\w+)/(?P<url_>.+)$', 'single_site',
        name='single_site'),
    url(r'^sites/theme/(?P<theme_id>\d+)$', 'site_theme',
        name='site_theme'),
)
