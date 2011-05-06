from django.conf.urls.defaults import patterns, url
from django.views.generic.simple import redirect_to
from input import OPINION_PRAISE, OPINION_ISSUE, OPINION_IDEA

urlpatterns = patterns('feedback.views',
    # These urls only support mobile, on desktop they redirect to /feedback
    url(r'^happy/?', 'give_feedback', {'type': OPINION_PRAISE.id},
        name='feedback.happy'),
    url(r'^sad/?', 'give_feedback', {'type': OPINION_ISSUE.id},
        name='feedback.sad'),
    url(r'^idea/?', 'give_feedback', {'type': OPINION_IDEA.id},
        name='feedback.idea'),

    # TODO: Implement new design on mobile pages and redirect these urls
    # url(r'^happy/?', redirect_to, {'url': '/feedback#happy'}),
    # url(r'^sad/?', redirect_to, {'url': '/feedback#sad'}),
    # url(r'^idea/?', redirect_to, {'url': '/feedback#idea'}),

    url(r'^thanks/?', 'thanks', name='feedback.thanks'),
    url(r'^feedback/?', 'feedback', name='feedback'),
    url(r'^download/?', 'download', name='feedback.download'),
    url(r'^opinion/(?P<id>\d+)$', 'opinion_detail', name='opinion.detail'),
)
