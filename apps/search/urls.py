from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

from feedback.models import Opinion

import views


urlpatterns = patterns('',
    url(r'^$', views.index, name='search'),
)
