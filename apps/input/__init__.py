from product_details import product_details
from product_details.version_compare import version_list
from tower import ugettext_lazy as _


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
}

OPINION_TYPES_USAGE = OPINION_PRAISE, OPINION_ISSUE, OPINION_IDEA
OPINION_TYPES = dict((type.id, type) for type in OPINION_TYPES_USAGE)


## Applications
class FIREFOX:
    id = 1
    short = 'firefox'
    pretty = _(u'Firefox')
    guid = '{ec8030f7-c20a-464f-9b0e-13a3a9e97384}'
    extra_versions = ['7.0a1', '6.0a2', '6.0a1', '5.0a2', '5.0']
    default_version = '5.0'  # Default dashboard version.
    beta_versions = version_list(
        dict(product_details.firefox_history_major_releases.items() +
             product_details.firefox_history_stability_releases.items() +
             product_details.firefox_history_development_releases.items()),
        hide_below='4.0b12',
        filter=(lambda v: v.is_beta)
    )
    release_versions = version_list(
        dict(product_details.firefox_history_major_releases.items() +
             product_details.firefox_history_stability_releases.items() +
             product_details.firefox_history_development_releases.items()),
        hide_below='4.0',
        filter=(lambda v: v.is_release)
    )


class MOBILE:
    id = 60
    short = 'mobile'
    pretty = _(u'Mobile')
    guid = '{a23983c0-fd0e-11dc-95ff-0800200c9a66}'
    extra_versions = ['7.0a1', '6.0a2', '6.0a1', '5.0a2', '5.0']
    default_version = '5.0'
    beta_versions = version_list(
        dict(product_details.mobile_history_major_releases.items() +
             product_details.mobile_history_stability_releases.items() +
             product_details.mobile_history_development_releases.items()),
        hide_below='4.0b1',
        filter=(lambda v: v.is_beta)
    )
    release_versions = version_list(
        dict(product_details.mobile_history_major_releases.items() +
             product_details.mobile_history_stability_releases.items() +
             product_details.mobile_history_development_releases.items()),
        hide_below='4.0',
        filter=(lambda v: v.is_release)
    )

PRODUCT_USAGE = _prods = (FIREFOX, MOBILE)
PRODUCTS = dict((prod.short, prod) for prod in _prods)
PRODUCT_IDS = dict((prod.id, prod) for prod in _prods)

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

key = 'LATEST_FIREFOX_RELEASED_DEVEL_VERSION'
LATEST_BETAS = {
    FIREFOX: (FIREFOX.beta_versions[0] if FIREFOX.beta_versions else
              product_details.firefox_versions[key]),
    MOBILE: (MOBILE.beta_versions[0] if MOBILE.beta_versions else
             product_details.mobile_details['beta_version']),
}

LATEST_RELEASE = {
    FIREFOX: (FIREFOX.release_versions[0] if FIREFOX.release_versions else
              product_details.firefox_versions['LATEST_FIREFOX_VERSION']),
    MOBILE: (MOBILE.release_versions[0] if MOBILE.release_versions else
              product_details.mobile_details['version']),
}


# Operating Systems
class WINDOWS_XP:
    pretty = _(u'Windows XP')
    short = 'winxp'
    ua_pattern = 'Windows NT 5.1'
    prods = set((FIREFOX,))


class WINDOWS_7:
    pretty = _(u'Windows 7')
    short = 'win7'
    ua_pattern = 'Windows NT 6.1'
    prods = set((FIREFOX,))


class WINDOWS_VISTA:
    pretty = _(u'Windows Vista')
    short = 'vista'
    ua_pattern = 'Windows NT 6.0'
    prods = set((FIREFOX,))


class OSX:
    pretty = _(u'Mac OS X')
    short = 'mac'
    ua_pattern = 'Mac'
    prods = set((FIREFOX,))


class MAEMO:
    pretty = _('Maemo')
    short = 'maemo'
    ua_pattern = 'Maemo'
    prods = set((MOBILE,))


class ANDROID:
    pretty = _('Android')
    short = 'android'
    ua_pattern = 'Android'
    prods = set((MOBILE,))


class LINUX:
    pretty = _(u'Linux')
    short = 'linux'
    ua_pattern = 'Linux'
    prods = set((FIREFOX,))


class PLATFORM_OTHER:
    pretty = _(u'Other')
    short = 'other'
    ua_pattern = None
    prods = set((FIREFOX, MOBILE))

PLATFORM_USAGE = _platforms = (WINDOWS_XP, WINDOWS_VISTA, WINDOWS_7, OSX,
                               MAEMO, ANDROID, LINUX)
PLATFORM_PATTERNS = [(p.ua_pattern, p.short) for p in PLATFORM_USAGE]
PLATFORMS = dict((platform.short, platform) for platform in _platforms)
