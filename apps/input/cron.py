import logging
import os
import urllib2

from django.conf import settings
from django.contrib.sites.models import Site

import cronjobs

log = logging.getLogger('reporter')

@cronjobs.register
def get_highcharts():
    """Fetch highcharts."""
    localfilename = os.path.join(settings.MEDIA_ROOT, 'js', 'libs',
                                 'highcharts.src.js')
    u = urllib2.urlopen('https://github.com/highslide-software/highcharts.com/'
                        'raw/2f27a00/js/highcharts.src.js')
    with open(localfilename, 'w') as f:
        f.write(u.read())


@cronjobs.register
def set_domains(desktop_domain, mobile_domain):
    """
    Set mobile domain names in sites framework.

    Example:
        ./manage.py cron set_domains example.com m.example.com

        ... sets the desktop domain to example.com, and the
        mobile domain to m.example.com.
    """
    # Not empty, please.
    try:
        assert desktop_domain
        assert mobile_domain
    except AssertionError:
        log.error('Desktop and mobile domains must not be empty.')
        return

    changes = {
        settings.DESKTOP_SITE_ID: desktop_domain,
        settings.MOBILE_SITE_ID: mobile_domain,
    }
    for id, domain in changes.items():
        site = Site.objects.get(id=id)
        site.domain = domain
        site.name = domain
        site.save()
        log.debug('Changed site %d domain to %s' % (id, domain))
