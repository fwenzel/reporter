from django.conf import settings

from product_details import product_details
from tower import ugettext_lazy as _

from input import urlresolvers
from feedback.version_compare import version_list


def get_channel():
    prefix = urlresolvers.get_url_prefix()
    if prefix and prefix.channel:
        return prefix.channel
    return settings.DEFAULT_CHANNEL


## Channels
class CHANNEL_RELEASE:
    short = 'release'
    pretty = _(u'Release Channel')


class CHANNEL_BETA:
    short = 'beta'
    pretty = _(u'Beta Channel')


class CHANNEL_NIGHTLY:
    short = 'nightly'
    pretty = _(u'Nightly Channel')

CHANNEL_USAGE = (CHANNEL_BETA, CHANNEL_RELEASE)
CHANNELS = dict((ch.short, ch) for ch in CHANNEL_USAGE)


## Known manufacturers and devices for mobile feedback.
KNOWN_MANUFACTURERS = (
    'Dell Inc.', 'HTC', 'LogicPD', 'Motorola', 'Nokia', 'Nokia', 'samsung',
    'SHARP', 'Sony Ericsson', 'TOSHIBA',
)
KNOWN_DEVICES = (
    'ADR6300', 'Dell Streak', 'Desire HD', 'Droid', 'DROID2', 'DROID2 GLOBAL',
    'DROIDX', 'GT-I9000', 'GT-I9000M', 'GT-I9000T', 'GT-P1000', 'GT-P1000L',
    'GT-P1000M', 'GT-P1000R', 'HD2 T8585', 'HTC bravo', 'HTC Desire',
    'HTC Glacier', 'HTC HD2', 'HTC Vision', 'IS03', 'LogicPD Zoom2', 'MB520',
    'MB860', 'Milestone', 'Nexus One', 'Nexus S', 'Nokia N900', 'PC36100',
    'SAMSUNG-SGH-I897', 'SC-01C', 'SC-02B', 'SCH-I500', 'SCH-I800', 'SGH-T849',
    'SGH-T959', 'SGH-T959D', 'SHW-M110S', 'SHW-M180S', 'SO-01B', 'SPH-D700',
    'SPH-P100', 'T-Mobile G2', 'TOSHIBA_FOLIO_AND_A', 'VEGAn-TAB-v1.0.0b4',
    'X10i',
)


## Opinion Type Length Restrictions
MAX_FEEDBACK_LENGTH = 140
MAX_IDEA_LENGTH = 250


## Opinion Types
class OPINION_PRAISE:
    id = 1
    short = 'praise'
    pretty = _(u'Praise')
    max_length = MAX_FEEDBACK_LENGTH


class OPINION_ISSUE:
    id = 2
    short = 'issue'
    pretty = _(u'Issue')
    max_length = MAX_FEEDBACK_LENGTH


class OPINION_IDEA:
    id = 3
    short = 'idea'
    pretty = _(u'Idea')
    max_length = MAX_IDEA_LENGTH


class OPINION_RATING:
    id = 4
    short = 'rating'
    pretty = _(u'Rating')
    max_length = MAX_FEEDBACK_LENGTH


class OPINION_BROKEN:
    id = 5
    short = 'brokenwebsite'
    pretty = _(u'Broken Website')
    max_length = MAX_FEEDBACK_LENGTH

op_types = {
    'OPINION_PRAISE': OPINION_PRAISE,
    'OPINION_ISSUE': OPINION_ISSUE,
    'OPINION_IDEA': OPINION_IDEA,
    'OPINION_RATING': OPINION_RATING,
    'OPINION_BROKEN': OPINION_BROKEN,
}

OPINION_TYPES_USAGE = (OPINION_PRAISE, OPINION_ISSUE, OPINION_IDEA,
                       OPINION_RATING, OPINION_BROKEN)
OPINION_TYPES = dict((type.id, type) for type in OPINION_TYPES_USAGE)


## Release Feedback: Rating Types
class RATING_STARTUP:
    id = 1
    short = 'startup'
    pretty = _(u'Start-Up Time')
    help = _(u'How long Firefox takes to start running')


class RATING_PAGELOAD:
    id = 2
    short = 'pageload'
    pretty = _(u'Page Load Time')
    help = _(u'How long it takes for web pages to load')


class RATING_RESPONSIVE:
    id = 3
    short = 'responsive'
    pretty = _(u'Responsiveness')
    help = _(u'How quickly web pages respond once they have loaded')


class RATING_CRASHY:
    id = 4
    short = 'crashy'
    pretty = _(u'Stability')
    help = _(u'How frequently Firefox crashes or loses data')


class RATING_FEATURES:
    id = 5
    short = 'features'
    pretty = _(u'Features')
    help = _(u"How well Firefox's built-in features serve your needs")

RATING_USAGE = (RATING_STARTUP, RATING_PAGELOAD, RATING_RESPONSIVE,
                RATING_CRASHY, RATING_FEATURES)
RATING_TYPES = dict((r.short, r) for r in RATING_USAGE)
RATING_IDS = dict((r.id, r) for r in RATING_USAGE)

RATING_CHOICES = (
    (1, _(u'Poor')),
    (2, _(u'Fair')),
    (3, _(u"Don't Care")),
    (4, _(u'Good')),
    (5, _(u'Excellent')),
)


## Applications
class FIREFOX:
    id = 1
    short = 'firefox'
    pretty = _(u'Firefox')
    guid = '{ec8030f7-c20a-464f-9b0e-13a3a9e97384}'
    beta_versions = version_list(
        product_details.firefox_history_development_releases,
        hide_below='4.0b1'
    )
    release_versions = version_list(
        dict(product_details.firefox_history_major_releases,
             **product_details.firefox_history_stability_releases),
        hide_below='3.6'  # TODO bump this once Firefox 4 ships.
    )


class MOBILE:
    id = 60
    short = 'mobile'
    pretty = _(u'Mobile')
    guid = '{a23983c0-fd0e-11dc-95ff-0800200c9a66}'
    beta_versions = version_list(
        product_details.mobile_history_development_releases,
        hide_below='4.0b1'
    )
    release_versions = version_list(
        dict(product_details.mobile_history_major_releases,
             **product_details.mobile_history_stability_releases),
        hide_below='4.0'
    )

PRODUCT_USAGE = _apps = (FIREFOX, MOBILE)
PRODUCTS = dict((app.short, app) for app in _apps)
PRODUCT_IDS = dict((app.id, app) for app in _apps)

UA_PATTERN_FIREFOX = (
    r'^Mozilla.*(Firefox|Minefield|Namoroka|Shiretoko|GranParadiso|BonEcho|'
    'Iceweasel|Fennec|MozillaDeveloperPreview)\/([^\s]*).*$')
UA_PATTERN_MOBILE = r'^Mozilla.*(Fennec)\/([^\s]*)$'

# Order is important: Since Fennec is Firefox too, it'll match the second
# pattern as well, so we must detect it first.
BROWSERS = (
    (MOBILE, UA_PATTERN_MOBILE),
    (FIREFOX, UA_PATTERN_FIREFOX),
)

LATEST_BETAS = {
    FIREFOX: product_details.firefox_versions[
        'LATEST_FIREFOX_RELEASED_DEVEL_VERSION'],
    MOBILE: product_details.mobile_details['beta_version'],
}

LATEST_RELEASE = {
    FIREFOX: product_details.firefox_versions['LATEST_FIREFOX_VERSION'],
    MOBILE: product_details.mobile_details['version'],
}


def LATEST_VERSION():
    return LATEST_BETAS if get_channel() == 'beta' else LATEST_RELEASE


# Operating Systems
class WINDOWS_XP:
    pretty = _(u'Windows XP')
    short = 'winxp'
    ua_pattern = 'Windows NT 5.1'
    apps = set((FIREFOX,))


class WINDOWS_7:
    pretty = _(u'Windows 7')
    short = 'win7'
    ua_pattern = 'Windows NT 6.1'
    apps = set((FIREFOX,))


class WINDOWS_VISTA:
    pretty = _(u'Windows Vista')
    short = 'vista'
    ua_pattern = 'Windows NT 6.0'
    apps = set((FIREFOX,))


class OSX:
    pretty = _(u'Mac OS X')
    short = 'mac'
    ua_pattern = 'Mac'
    apps = set((FIREFOX,))


class MAEMO:
    pretty = _('Maemo')
    short = 'maemo'
    ua_pattern = 'Maemo'
    apps = set((MOBILE,))


class ANDROID:
    pretty = _('Android')
    short = 'android'
    ua_pattern = 'Android'
    apps = set((MOBILE,))


class LINUX:
    pretty = _(u'Linux')
    short = 'linux'
    ua_pattern = 'Linux'
    apps = set((FIREFOX,))


class PLATFORM_OTHER:
    pretty = _(u'Other')
    short = 'other'
    ua_pattern = None
    apps = set((FIREFOX, MOBILE))

PLATFORM_USAGE = _platforms = (WINDOWS_XP, WINDOWS_VISTA, WINDOWS_7, OSX, MAEMO, 
                               ANDROID, LINUX)
PLATFORM_PATTERNS = [(p.ua_pattern, p.short) for p in PLATFORM_USAGE]
PLATFORMS = dict((platform.short, platform) for platform in _platforms)
