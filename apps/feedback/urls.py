from django.conf.urls.defaults import patterns, url
from django.views.generic.simple import redirect_to
from input import OPINION_PRAISE, OPINION_ISSUE, OPINION_IDEA

urlpatterns = patterns('feedback.views',
    url(r'^happy/?', redirect_to, {'url': '/feedback#happy'}),
    url(r'^sad/?', redirect_to, {'url': '/feedback#sad'}),
    url(r'^idea/?', redirect_to, {'url': '/feedback#idea'}),

    url(r'^thanks/?', 'thanks', name='feedback.thanks'),
    url(r'^feedback/?', 'feedback', name='feedback'),
    url(r'^download/?', 'download', name='feedback.download'),
    url(r'^opinion/(?P<id>\d+)$', 'opinion_detail', name='opinion.detail'),
)
