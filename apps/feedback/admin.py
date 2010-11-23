from django.contrib import admin

from .models import Opinion, Term
from .utils import smart_truncate


class OpinionAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    list_display = ('type', 'truncated_description', 'created',
                    'product_name', 'version', 'os_name', 'locale',
                    'manufacturer', 'device')
    list_display_links = ('truncated_description',)
    list_filter = ('type', 'version', 'os', 'locale', 'manufacturer',
                   'device')
    ordering = ('-created',)
    search_fields = ['description']

    fieldsets = (
        (None, {
            'fields': ('type', 'description', 'created')
        }),
        ('Build Info', {
            'fields': ('user_agent', 'product_name', 'version', 'os_name',
                       'locale')
        }),
        ('Device Info', {
            'fields': ('manufacturer', 'device')
        }),
        ('Terms', {
            'fields': ('terms',)
        }),
    )
    readonly_fields = ('created', 'product_name', 'os_name', 'version',
                       'locale')

admin.site.register(Opinion, OpinionAdmin)


class TermAdmin(admin.ModelAdmin):
    list_display = ('term', 'hidden')
    list_filter = ('hidden',)
    search_fields = ['term']
admin.site.register(Term, TermAdmin)
