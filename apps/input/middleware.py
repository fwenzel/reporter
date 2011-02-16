import urllib

from django.conf import settings
from django.contrib.sites.models import Site
from django.http import HttpResponsePermanentRedirect
from django.utils.encoding import smart_str

from caching.base import cached
import tower

from input import FIREFOX, MOBILE
from input import urlresolvers
from input.helpers import urlparams


class LocaleAndChannelURLMiddleware(object):
    """
    1. Search for the locale.
    2. Save it in the request.
    3. Strip them from the URL.
    """

    def process_request(self, request):
        prefixer = urlresolvers.Prefixer(request)
        urlresolvers.set_url_prefix(prefixer)
        full_path = prefixer.fix(prefixer.shortened_path)

        # Lang and channel are changeable by GET request.
        # Note that some paths might not exist across all channels, so handle
        # with care.
        # Format is (GET parameter, prefixer attribute)
        for param, attr in (('lang', 'locale'), ('channel', 'channel')):
            if param in request.GET:
                # Blank out the prefixer attribute so that we can set a new
                # one. Remove the parameter from the query params so we don't
                # have an infinite loop.
                setattr(prefixer, attr, '')
                new_path = prefixer.fix(prefixer.shortened_path)
                query = dict((smart_str(k), request.GET[k]) for k in
                             request.GET)
                query.pop(param)
                return HttpResponsePermanentRedirect(urlparams(new_path,
                                                               **query))

        if full_path != request.path:
            query_string = request.META.get('QUERY_STRING', '')
            full_path = urllib.quote(full_path.encode('utf-8'))

            if query_string:
                full_path = '%s?%s' % (full_path, query_string)

            response = HttpResponsePermanentRedirect(full_path)

            # Vary on Accept-Language if we changed the locale
            old_locale = prefixer.locale
            new_locale, new_channel, _ = prefixer.split_path(full_path)
            if old_locale != new_locale:
                response['Vary'] = 'Accept-Language'

            return response

        request.path_info = '/' + prefixer.shortened_path
        request.locale = prefixer.locale
        request.channel = prefixer.channel
        tower.activate(prefixer.locale)


class MobileSiteMiddleware(object):
    """
    Change the settings.SITE_ID to match the request.META['HTTP_HOST'].
    Used to detect our Mobile site from the URL.
    Borrowed from http://code.djangoproject.com/ticket/4438

    Also forwards known mobile devices to the mobile site.
    """

    def process_request(self, request):
        try:
            domain = request.META['HTTP_HOST']
            site = cached(lambda: Site.objects.get(domain=domain),
                          ''.join((settings.CACHE_PREFIX, 'dom:', domain)),
                          settings.CACHE_COUNT_TIMEOUT)
        except (Site.DoesNotExist, KeyError):
            # If Site ID picked in header, serve that, otherwise default
            # to Desktop site.
            site_header = request.META.get('SITE_ID')
            if site_header in (settings.DESKTOP_SITE_ID,
                               settings.MOBILE_SITE_ID):
                settings.SITE_ID = site_header
            else:
                settings.SITE_ID = settings.DESKTOP_SITE_ID
        else:
            settings.SITE_ID = site.id

        # Keep mobile site status in request object
        request.mobile_site = (settings.SITE_ID == settings.MOBILE_SITE_ID)
        request.default_prod = request.mobile_site and MOBILE or FIREFOX
