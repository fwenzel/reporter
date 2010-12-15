from tower import ugettext_lazy as _


# Known manufacturers and devices for mobile feedback.
KNOWN_MANUFACTURERS = ('Samsung', 'HTC', 'Motorola', 'LG', 'Sony')
KNOWN_DEVICES = ('Hero', 'Vibrant', 'Droid', 'Epic', 'Evo', 'Desire',
                 'Desire Z', 'Droid Incredible', 'Desire HD', 'EVO 4G',
                 'Nexus One', 'Optimus Z', 'Droid 2', 'Droid X', 'Galaxy Tab')

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
