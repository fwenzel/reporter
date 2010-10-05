from django.contrib import admin
from django.shortcuts import redirect
from django.views import debug

import jingo

import themes.tasks


@admin.site.admin_view
def recluster(request):
    if request.method == 'POST':
        themes.tasks.recluster.delay()
        return redirect('myadmin.recluster')

    return jingo.render(request, 'myadmin/recluster.html')


@admin.site.admin_view
def settings(request):
    settings_dict = debug.get_safe_settings()

    return jingo.render(request, 'myadmin/settings.html',
                        {'settings_dict': settings_dict})

