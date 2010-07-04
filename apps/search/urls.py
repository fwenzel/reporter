from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

from haystack.query import SearchQuerySet

from feedback.models import Opinion

import views


sqs = SearchQuerySet().models(Opinion)

urlpatterns = patterns('',
    url(r'^$', views.index, name='search'),
)
