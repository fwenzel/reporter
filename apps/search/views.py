from haystack.views import SearchView
import jingo

from feedback.models import Opinion, Term
from feedback import stats, FIREFOX


class OpinionSearchView(SearchView):
    def get_results(self):
        """If no query is selected, browse dataset."""
        if self.form.is_valid() and not self.query:
            return Opinion.objects.browse(**self.form.cleaned_data)
        else:
            return super(OpinionSearchView, self).get_results()

    def extra_context(self):
        """Gather sentiments/trends/demographic info for these search results."""
        extra = super(OpinionSearchView, self).extra_context()

        # TODO make sure this won't issue millions of queries
        opinion_pks = [ res.pk for res in self.results ]

        # Aggregates:
        opinions = Opinion.objects.filter(pk__in=opinion_pks)

        extra['sent'] = stats.sentiment(qs=opinions)
        extra['demo'] = stats.demographics(qs=opinions)

        frequent_terms = Term.objects.frequent().filter(
            used_in__in=opinion_pks)[:20]
        extra['terms'] = stats.frequent_terms(qs=frequent_terms)

        return extra

    def create_response(self):
        """
        Generates the actual HttpResponse to send back to the user.

        The same as Haystack's stock SearchView, except for Jinja2 rendering.
        """
        (paginator, page) = self.build_page()

        context = {
            'query': self.query,
            'form': self.form,
            'page': page,
            'paginator': paginator,
        }
        context.update(self.extra_context())
        return jingo.render(self.request, self.template, context)
