import product_details
from tower import ugettext_lazy as _


# Applications, shamelessly snagged from AMO
class FIREFOX:
    id = 1
    short = 'firefox'
    pretty = _(u'Firefox')
    guid = '{ec8030f7-c20a-464f-9b0e-13a3a9e97384}'
    hide_below = '3.6.4build7'

class MOBILE:
    id = 60
    short = 'mobile'
    pretty = _(u'Mobile')
    guid = '{a23983c0-fd0e-11dc-95ff-0800200c9a66}'

APP_USAGE = _apps = (FIREFOX, MOBILE)
APPS = dict((app.short, app) for app in _apps)
APP_IDS = dict((app.id, app) for app in _apps)

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
    FIREFOX: product_details.firefox_versions['LATEST_FIREFOX_DEVEL_VERSION'],
    MOBILE: product_details.mobile_details['beta_version'],
}

# Operating Systems
class WINDOWS_XP:
    pretty = _(u'Windows XP')
    short = 'winxp'
    ua_pattern = 'Windows NT 5.1'

class WINDOWS_7:
    pretty = _(u'Windows 7')
    short = 'win7'
    ua_pattern = 'Windows NT 6.1'

class WINDOWS_VISTA:
    pretty = _(u'Windows Vista')
    short = 'vista'
    ua_pattern = 'Windows NT 6.0'

class OSX:
    pretty = _(u'Mac OS X')
    short = 'mac'
    ua_pattern = 'Mac'

class LINUX:
    pretty = _(u'Linux')
    short = 'linux'
    ua_pattern = 'Linux'

class OS_OTHER:
    pretty = _(u'Other')
    short = 'other'
    ua_pattern = None

OS_USAGE = _oses = (WINDOWS_XP, WINDOWS_VISTA, WINDOWS_7, OSX, LINUX)
OS_PATTERNS = [ (o.ua_pattern, o.short) for o in OS_USAGE ]
OSES = dict((os.short, os) for os in _oses)
