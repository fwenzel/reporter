from haystack.views import SearchView

from feedback.models import Opinion, Term
from feedback import stats


class OpinionSearchView(SearchView):
    def extra_context(self):
        """Gather sentiments/trends/demographic info for these search results."""
        extra = super(OpinionSearchView, self).extra_context()

        # TODO make sure this won't issue millions of queries
        opinion_pks = [ res.pk for res in self.results ]

        # TODO (default) time restrictions
        # Aggregates:
        opinions = Opinion.objects.filter(pk__in=opinion_pks)

        extra['sent'] = stats.sentiment(qs=opinions)
        extra['demographics'] = stats.demographics(qs=opinions)

        frequent_terms = Term.objects.frequent().filter(
            used_in__in=opinion_pks)[:20]
        extra['terms'] = stats.frequent_terms(qs=frequent_terms)

        return extra
