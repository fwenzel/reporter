from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('website_issues.views',
    # TODO: Split this into beta and release.
    url(r'^beta/sites/?$', 'website_issues', name='website_issues'),
    url(r'^beta/site/(?P<protocol>\w+)/(?P<url_>.+)$', 'single_site',
        name='single_site'),
    url(r'^beta/sites/theme/(?P<theme_id>\d+)$', 'site_theme',
        name='site_theme'),
)
