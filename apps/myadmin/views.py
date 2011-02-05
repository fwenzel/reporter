from django.contrib import admin
from django.shortcuts import redirect
from django.views import debug

import jingo

import api.tasks
import themes.tasks


# TODO(davedash): remove when metrics.json is in place
@admin.site.admin_view
def recluster(request):
    if request.method == 'POST':
        themes.tasks.recluster.delay()
        return redirect('myadmin.recluster')

    return jingo.render(request, 'myadmin/recluster.html')


@admin.site.admin_view
def export_tsv(request):
    if request.method == 'POST':
        api.tasks.export_tsv.delay()
        data = {'exporting': True}
    else:
        data = {}

    return jingo.render(request, 'myadmin/export_tsv.html', data)


@admin.site.admin_view
def settings(request):
    settings_dict = debug.get_safe_settings()

    return jingo.render(request, 'myadmin/settings.html',
                        {'settings_dict': settings_dict})

