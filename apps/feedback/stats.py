from django.db.models import Count

from . import OSES, OS_OTHER
from .models import Opinion, Term


def demographics(qs=None):
    """Get an OS/Locale summary as a list of dicts."""
    if qs is None:
        opinions = Opinion.objects.all()
    else:
        opinions = qs

    # Summarize OSes.
    per_os = opinions.values('os').annotate(cnt=Count('pk')).order_by('-cnt')
    os_name = lambda short: OSES.get(short, OS_OTHER).pretty
    os_data = [ {'os': item['os'],
                 'name': os_name(item['os']),
                 'count': item['cnt']} for item in per_os ]

    # Summarize locales.
    per_locale = opinions.values('locale').annotate(cnt=Count('pk')).order_by(
        '-cnt')
    locale_data = [ {'locale': item['locale'],
                     'count': item['cnt']} for item in per_locale ]

    return {
        'os': os_data,
        'locale': locale_data
    }


def frequent_terms(count=10, qs=None):
    """Get frequent terms and their weights as a list of dicts."""
    if qs is None:
        frequent_terms = Term.objects.frequent()[:count]
    else:
        frequent_terms = qs

    if not frequent_terms:
        terms = []
    else:
        max_weight = frequent_terms[0].cnt
        terms = [
            {'term': ft.term,
             'count': ft.cnt,
             'weight': int(float(ft.cnt) / max_weight * 5)} for
            ft in frequent_terms ]
    return terms


def sentiment(qs=None):
    """Get aggregates on the number of positive/negative sentiments."""
    if qs is None:
        opinions = Opinion.objects.all()
    else:
        opinions = qs

    total = opinions.count()
    sad = opinions.filter(positive=False).aggregate(cnt=Count('pk'))['cnt']
    happy = total - sad
    return {
        'sentiment': sad > happy and 'sad' or 'happy',
        'total': total,
        'sad': sad,
        'happy': happy,
    }
