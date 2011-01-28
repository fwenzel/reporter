from django.conf import settings

from tower import ugettext_lazy as _

from input import urlresolvers


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

CHANNEL_USAGE = (CHANNEL_BETA, CHANNEL_RELEASE)  # TODO add nightly
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


## Opinion Types
class OPINION_PRAISE:
    id = 1
    short = 'praise'
    pretty = _(u'Praise')
    max_length = settings.MAX_FEEDBACK_LENGTH


class OPINION_ISSUE:
    id = 2
    short = 'issue'
    pretty = _(u'Issue')
    max_length = settings.MAX_FEEDBACK_LENGTH


class OPINION_SUGGESTION:
    id = 3
    short = 'suggestion'
    pretty = _(u'Suggestion')
    max_length = settings.MAX_SUGGESTION_LENGTH


class OPINION_RATING:
    id = 4
    short = 'rating'
    pretty = _(u'Rating')
    max_length = settings.MAX_FEEDBACK_LENGTH


class OPINION_BROKEN:
    id = 5
    short = 'brokenwebsite'
    pretty = _(u'Broken Website')
    max_length = settings.MAX_FEEDBACK_LENGTH

op_types = {
    'OPINION_PRAISE': OPINION_PRAISE,
    'OPINION_ISSUE': OPINION_ISSUE,
    'OPINION_SUGGESTION': OPINION_SUGGESTION,
    'OPINION_RATING': OPINION_RATING,
    'OPINION_BROKEN': OPINION_BROKEN,
}

OPINION_TYPES_USAGE = (OPINION_PRAISE, OPINION_ISSUE, OPINION_SUGGESTION,
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
