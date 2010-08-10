from django.conf.urls.defaults import patterns, url

urlpatterns = patterns('feedback.views',
    url(r'^sad/?', 'give_feedback', {'positive': False},
        name='feedback.sad'),
    url(r'^happy/?', 'give_feedback', {'positive': True},
        name='feedback.happy'),
    url(r'^thanks/?', 'thanks', name='feedback.thanks'),
    url(r'^download/?', 'need_beta', name='feedback.need_beta'),
    url(r'^clusters/?$', 'clusters', name='clusters'),
    url(r'^cluster/(?P<feeling>[^/]+)/(?P<platform>[^/]+)/(?P<version>[^/]+)/'
        '(?P<frequency>[^/]+)$',
        'cluster', name='cluster'),
    url(r'^opinion/(?P<id>\d+)$', 'opinion_detail', name='opinion.detail'),
)
