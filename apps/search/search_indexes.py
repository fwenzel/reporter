from urlparse import urlparse

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

    def prepare_text(self, obj):
        """Include URL parts in searchable text."""
        indexable = [obj.description]
        if obj.url:
            parsed = urlparse(obj.url)
            # Domain
            domain_split = parsed.netloc.split('.')
            if domain_split and domain_split[0] == 'www':
                indexable += domain_split[1:]
                indexable.append('.'.join(domain_split[1:]))
            else:
                indexable += domain_split
                indexable.append(parsed.netloc)

            # Path
            indexable += parsed.path.split('/')
        return "\n".join(indexable)

site.register(Opinion, OpinionIndex)
