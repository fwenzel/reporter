from django.conf.urls.defaults import *

import jingo

urlpatterns = patterns('',
    url(r'^sad/?', 'feedback.views.give_feedback', {'positive': False},
        name='feedback.sad'),
    url(r'^happy/?', 'feedback.views.give_feedback', {'positive': True},
        name='feedback.happy'),
    url(r'^thanks/?', jingo.render, {'template': 'feedback/thanks.html'},
        name='feedback.thanks'),
    url(r'^download/?', jingo.render, {'template': 'feedback/need_beta.html'},
        name='feedback.need_beta'),
)
