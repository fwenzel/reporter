from .models import Term


def frequent_terms(count=10, qs=None):
    """Get frequent terms and their weights as a list of dicts."""
    frequent_terms = qs or Term.objects.frequent()[:count]

    terms = []

    if frequent_terms:
        max_weight = frequent_terms[0].cnt
        for ft in frequent_terms:
            terms.append(dict(term=ft.term, count=ft.cnt,
                              weight=int(float(ft.cnt) / max_weight * 5)))
    return terms
