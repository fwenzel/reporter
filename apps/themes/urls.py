from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('themes.views',
    url(r'^themes/?$', 'index', name='themes'),
    url(r'^themes/(?P<theme_id>\d+)/?$', 'theme', name='theme'),
)
