from django.conf.urls.defaults import patterns, url


urlpatterns = patterns('dashboard.views',
    url(r'^ajax/sentiment/(?P<period>\w{2})/?', 'sentiment'),
    url(r'^ajax/trends/(?P<period>\w{2})/?', 'trends'),
    url(r'^ajax/demographics/(?P<period>\w{2})/?', 'demographics'),
    url(r'^ajax/messages/?', 'messages'),
)
