from haystack.views import SearchView


class OpinionSearchView(SearchView):
    def extra_context(self):
        """Gather sentiments/trends/demographic info for these search results."""
        extra = super(OpinionSearchView, self).extra_context()

        # TODO make sure this won't issue millions of queries
        opinion_pks = [ res.pk for res in self.results ]

        # TODO build aggregates

        return extra
