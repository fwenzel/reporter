from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('themes.views',
    # TODO: Split this into beta, releases.
    url(r'^beta/themes/?$', 'index', name='themes'),
    url(r'^beta/themes/(?P<theme_id>\d+)/?$', 'theme', name='theme'),
)
