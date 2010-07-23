import urllib

from django.conf import settings
from django.contrib.sites.models import Site
from django.http import HttpResponsePermanentRedirect
from django.utils.encoding import smart_str

import tower

from feedback import FIREFOX, MOBILE
from . import urlresolvers
from .helpers import urlparams


class LocaleURLMiddleware(object):
    """
    1. Search for the locale.
    2. Save it in the request.
    3. Strip them from the URL.
    """

    def process_request(self, request):
        prefixer = urlresolvers.Prefixer(request)
        urlresolvers.set_url_prefix(prefixer)
        full_path = prefixer.fix(prefixer.shortened_path)

        if 'lang' in request.GET:
            # Blank out the locale so that we can set a new one. Remove lang
            # from the query params so we don't have an infinite loop.
            prefixer.locale = ''
            new_path = prefixer.fix(prefixer.shortened_path)
            query = dict((smart_str(k), request.GET[k]) for k in request.GET)
            query.pop('lang')
            return HttpResponsePermanentRedirect(urlparams(new_path, **query))

        if full_path != request.path:
            query_string = request.META.get('QUERY_STRING', '')
            full_path = urllib.quote(full_path.encode('utf-8'))

            if query_string:
                full_path = '%s?%s' % (full_path, query_string)

            response = HttpResponsePermanentRedirect(full_path)

            # Vary on Accept-Language if we changed the locale
            old_locale = prefixer.locale
            new_locale, _ = prefixer.split_path(full_path)
            if old_locale != new_locale:
                response['Vary'] = 'Accept-Language'

            return response

        request.path_info = '/' + prefixer.shortened_path
        request.locale = prefixer.locale
        tower.activate(prefixer.locale)


class MobileSiteMiddleware(object):
    """
    Change the settings.SITE_ID to match the request.META['HTTP_HOST'].
    Used to detect our Mobile site from the URL.

    Borrowed from http://code.djangoproject.com/ticket/4438
    """

    def process_request(self, request):
        try:
            site = Site.objects.get(domain=request.META['HTTP_HOST'])
        except Site.DoesNotExist:
            # Keep existing setting
            settings.SITE_ID = settings.DESKTOP_SITE_ID
        else:
            settings.SITE_ID = site.id

        # Keep mobile site status in request object
        request.mobile_site = (settings.SITE_ID == settings.MOBILE_SITE_ID)
        request.default_app = request.mobile_site and MOBILE or FIREFOX
