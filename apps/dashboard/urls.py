from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('dashboard.views',
    url(r'^$', 'dashboard', name='dashboard'),
)
