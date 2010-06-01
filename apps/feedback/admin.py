from django.contrib import admin

from .models import Opinion, Term
from .utils import smart_truncate


class OpinionAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    list_display = ('positive', 'truncated_description', 'created',
                    'product_name', 'version', 'os_name', 'locale')
    list_display_links = ('truncated_description',)
    list_filter = ('positive', 'version', 'os', 'locale')
    ordering = ('-created',)

    fieldsets = (
        (None, {
            'fields': ('positive', 'description', 'created')
        }),
        ('Build Info', {
            'fields': ('user_agent', 'product_name', 'version', 'os_name',
                       'locale')
        }),
        ('Terms', {
            'fields': ('terms',)
        }),
    )
    readonly_fields = ('created', 'product_name', 'os_name')

admin.site.register(Opinion, OpinionAdmin)


class TermAdmin(admin.ModelAdmin):
    list_display = ('term', 'hidden')
    list_filter = ('hidden',)
admin.site.register(Term, TermAdmin)
