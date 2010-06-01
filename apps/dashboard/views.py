import datetime

from django.db.models import Count

from annoying.decorators import ajax_request, render_to

from feedback.models import Opinion, Term
from .forms import SearchForm, PeriodForm, PERIOD_DELTAS


@render_to('dashboard/dashboard.html')
def dashboard(request):
    form = SearchForm()
    period = PeriodForm()
    return {'form': form, 'period': period}


def period_to_date(f):
    """Decorator translating period string to dates."""
    def wrapped(request, *args, **kwargs):
        period = request.GET.get('period', '1d')
        delta = PERIOD_DELTAS.get(period, datetime.timedelta(days=1))
        start = datetime.datetime.now() - delta
        return f(request, date_start=start, date_end=None)
    return wrapped


@ajax_request
@period_to_date
def sentiment(request, date_start, date_end):
    opinions = lambda pos: Opinion.objects.between(
        date_start, date_end).filter(positive=pos).aggregate(
            cnt=Count('pk'))['cnt']
    sad = opinions(False)
    happy = opinions(True)
    return {
        'sentiment': sad > happy and 'sad' or 'happy',
        'total': sad+happy,
        'sad': sad,
        'happy': happy,
    }


@ajax_request
@period_to_date
def trends(request, date_start, date_end):
    frequent_terms = Term.objects.visible().filter(
        used_in__in=Opinion.objects.between(date_start, date_end)).annotate(
        cnt=Count('used_in')).order_by('-cnt')[:10]
    if not frequent_terms:
        return {'terms': []}
    else:
        max_weight = frequent_terms[0].cnt
        return {'terms': [
            {'term': ft.term,
             'weight': round(float(ft.cnt) / max_weight * 5)} for
            ft in frequent_terms ]}


@ajax_request
@period_to_date
def demographics(request, date_start, date_end):
    opinions = Opinion.objects.filter(
        created__gte=date_start, created__lte=date_end)
