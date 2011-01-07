from django.conf.urls.defaults import patterns, url

from feedback import OPINION_PRAISE, OPINION_ISSUE, OPINION_SUGGESTION

urlpatterns = patterns('feedback.views',
    url(r'^happy/?', 'give_feedback', {'type': OPINION_PRAISE},
        name='feedback.happy'),
    url(r'^sad/?', 'give_feedback', {'type': OPINION_ISSUE},
        name='feedback.sad'),
    url(r'^suggestion/?', 'give_feedback', {'type': OPINION_SUGGESTION},
        name='feedback.suggestion'),
    url(r'^feedback/beta/?', 'beta_feedback', name='feedback.beta_feedback'),
    url(r'^feedback/?', 'release_feedback', name='feedback.release_feedback'),
    url(r'^thanks/?', 'thanks', name='feedback.thanks'),
    url(r'^download/beta/?', 'need_beta', name='feedback.need_beta'),
    url(r'^download/?', 'need_release', name='feedback.need_release'),
    url(r'^opinion/(?P<id>\d+)$', 'opinion_detail', name='opinion.detail'),
)
