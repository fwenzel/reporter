from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('themes.views',
                       url(r'^$', 'index', name='themes'),
                      )
