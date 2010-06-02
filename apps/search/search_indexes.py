from haystack.indexes import *
from haystack import site

from feedback.models import Opinion


class OpinionIndex(SearchIndex):
    text = CharField(document=True, model_attr='description')
    created = DateTimeField(model_attr='created')

site.register(Opinion, OpinionIndex)
