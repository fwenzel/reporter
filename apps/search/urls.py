from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

from haystack.query import SearchQuerySet

from feedback.models import Opinion

from .forms import ReporterSearchForm
from .views import OpinionSearchView


sqs = SearchQuerySet().models(Opinion)

urlpatterns = patterns('',
    url(r'^$', OpinionSearchView(searchqueryset=sqs,
                                 form_class=ReporterSearchForm),
        name='search'),
)
