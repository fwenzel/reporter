from tower import ugettext_lazy as _


# Known manufacturers and devices for mobile feedback.
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

# Stable Feedback: Rating Types
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
    pretty = _(u'Crashiness')
    help = _(u'How frequently Firefox crashes or loses data')

class RATING_FEATURES:
    id = 5
    short = 'features'
    pretty = _(u'Features')
    help = _(u"How well Firefox's built-in features serve your needs")

RATING_USAGE = (RATING_STARTUP, RATING_PAGELOAD, RATING_RESPONSIVE,
                RATING_CRASHY, RATING_FEATURES)
RATING_TYPES = dict((r.short, r) for r in RATING_USAGE)

RATING_CHOICES = (
    (1, _(u'Poor')),
    (2, _(u'Fair')),
    (3, _(u"Don't Care")),
    (4, _(u'Good')),
    (5, _(u'Excellent')),
)
