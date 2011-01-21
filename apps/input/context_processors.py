from django.conf import settings
from django.utils import translation

from input import get_channel, op_types


def input(request):
    return dict(settings=settings, CHANNEL=get_channel())


def i18n(request):
    return {'LANGUAGES': settings.LANGUAGES,
            'LANG': settings.LANGUAGE_URL_MAP.get(translation.get_language())
                    or translation.get_language(),
            'DIR': 'rtl' if translation.get_language_bidi() else 'ltr',
            }


def mobile(request):
    return {'MOBILE': getattr(request, 'mobile_site', False)}


def opinion_types(request):
    return op_types
