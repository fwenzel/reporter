from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    (r'^$', direct_to_template, {'template': 'feedback/dashboard.html'}),

    # Feedback actions
    url(r'^sad/?', 'feedback.views.give_feedback', {'positive': False},
        name='feedback.sad'),
    url(r'^thanks/?', direct_to_template, {'template': 'feedback/thanks.html'},
        name='feedback.thanks'),

    # Uncomment the next line to enable the admin:
    # (r'^admin/', include(admin.site.urls)),
)
