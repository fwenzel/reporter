from django.conf.urls.defaults import patterns, url

from feedback import OPINION_PRAISE, OPINION_ISSUE, OPINION_SUGGESTION


urlpatterns = patterns('feedback.views',
    # TODO: combine all beta feedback submissions into beta/feedback. Bug 623364.
    url(r'^happy/?', 'give_feedback', {'type': OPINION_PRAISE},
        name='feedback.happy'),
    url(r'^sad/?', 'give_feedback', {'type': OPINION_ISSUE},
        name='feedback.sad'),
    url(r'^suggestion/?', 'give_feedback', {'type': OPINION_SUGGESTION},
        name='feedback.suggestion'),

    url(r'^beta/feedback/?', 'beta_feedback', name='feedback.beta_feedback'),
    url(r'^beta/thanks/?', 'thanks', name='feedback.thanks'),

    url(r'^release/feedback/?', 'release_feedback', name='feedback.release_feedback'),

    url(r'^release/download/?', 'need_release', name='feedback.need_release'),
    url(r'^beta/download/?', 'need_beta', name='feedback.need_beta'),

    # TODO Should this be under beta/release/etc.?
    url(r'^opinion/(?P<id>\d+)$', 'opinion_detail', name='opinion.detail'),
)
