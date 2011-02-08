from django.conf.urls.defaults import patterns, url

from input import OPINION_PRAISE, OPINION_ISSUE, OPINION_SUGGESTION


urlpatterns = patterns('feedback.views',
    # TODO: combine all beta feedback submissions into beta/feedback.
    # Bug 623364.
    url(r'^happy/?', 'give_feedback', {'type': OPINION_PRAISE.id},
        name='feedback.happy'),
    url(r'^sad/?', 'give_feedback', {'type': OPINION_ISSUE.id},
        name='feedback.sad'),
    url(r'^suggestion/?', 'give_feedback', {'type': OPINION_SUGGESTION.id},
        name='feedback.suggestion'),

    url(r'^thanks/?', 'thanks', name='feedback.thanks'),

    url(r'^feedback/?', 'feedback', name='feedback'),

    url(r'^download/?', 'download', name='feedback.download'),

    url(r'^opinion/(?P<id>\d+)$', 'opinion_detail', name='opinion.detail'),
)
