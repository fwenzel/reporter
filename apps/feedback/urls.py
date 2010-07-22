from django.conf.urls.defaults import *

import jingo

urlpatterns = patterns('feedback.views',
    url(r'^sad/?', 'give_feedback', {'positive': False},
        name='feedback.sad'),
    url(r'^happy/?', 'give_feedback', {'positive': True},
        name='feedback.happy'),
    url(r'^thanks/?', jingo.render, {'template': 'feedback/thanks.html'},
        name='feedback.thanks'),
    url(r'^download/?', 'need_beta', name='feedback.need_beta'),
)
