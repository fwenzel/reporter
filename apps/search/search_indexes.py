from haystack.indexes import *
from haystack import site

from feedback.models import Opinion


class OpinionIndex(SearchIndex):
    text = CharField(document=True, model_attr='description')
    created = DateTimeField(model_attr='created')

    positive = BooleanField(model_attr='positive')
    product = IntegerField(model_attr='product')
    version = CharField(model_attr='version')
    os = CharField(model_attr='os')
    locale = CharField(model_attr='locale')

site.register(Opinion, OpinionIndex)
