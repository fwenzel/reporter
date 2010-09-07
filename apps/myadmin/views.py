from django.shortcuts import redirect

import jingo

import themes.tasks


def recluster(request):
    if request.method == 'POST':
        themes.tasks.recluster.delay()
        return redirect('myadmin.recluster')

    return jingo.render(request, 'myadmin/recluster.html')
