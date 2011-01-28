import datetime
import random

from django.conf import settings
from django.db import transaction

import cronjobs

import input
from feedback.models import Opinion, Rating

DEFAULT_NUM_OPINIONS = 100
TYPES = list(input.OPINION_TYPES_USAGE)
URLS = ['http://google.com', 'http://mozilla.com', 'http://bit.ly', '', '']
text = """
    To Sherlock Holmes she is always the woman. I have seldom heard him mention
    her under any other name. In his eyes she eclipses and predominates the
    whole of her sex. It was not that he felt any emotion akin to love for
    Irene Adler. All emotions, and that one particularly, were abhorrent to his
    cold, precise but admirably balanced mind. He was, I take it, the most
    perfect reasoning and observing machine that the world has seen, but as a
    lover he would have placed himself in a false position. He never spoke of
    the softer passions, save with a gibe and a sneer. They were admirable
    things for the observer-excellent for drawing the veil from men's motives
    and actions. But for the trained reasoner to admit such intrusions into his
    own delicate and finely adjusted temperament was to introduce a distracting
    factor which might throw a doubt upon all his mental results. Grit in a
    sensitive instrument, or a crack in one of his own high-power lenses, would
    not be more disturbing than a strong emotion in a nature such as his. And
    yet there was but one woman to him, and that woman was the late Irene
    Adler, of dubious and questionable memory.
    """

sample = lambda: ' '.join(random.sample(text.split(), 15))
UA_STRINGS = {'mobile': ['Mozilla/5.0 (Android; Linux armv71; rv:2.0b6pre)'
                         ' Gecko/20100924 Namoroka/4.0b7pre Fennec/2.0b1pre'],
              'desktop': ['Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; '
                          'fr-FR; rv:2.0b1) Gecko/20100628 Firefox/4.0b1',

                          'Mozilla/5.0 (Windows; U; Windows NT 5.1; '
                          'en-US; rv:1.9.2.4) Gecko/20100611 Firefox/3.6.13 '
                          '(.NET CLR 3.5.30729)',

                          'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; '
                          'fr-FR; rv:2.0b1) Gecko/20100628 Firefox/3.6.13',

                          ]}
DEVICES = dict(Samsung='Epic Vibrant Transform'.split(),
               HTC='Evo Hero'.split(),
               Motorola='DroidX Droid2'.split())


@cronjobs.register
@transaction.commit_on_success
def populate(num_opinions=None, product='mobile', type=None):
    if not num_opinions:
        num_opinions = getattr(settings, 'NUM_FAKE_OPINIONS',
                               DEFAULT_NUM_OPINIONS)

    if type:
        type = type.id

    for i in xrange(num_opinions):
        if not type:
            type = random.choice(TYPES).id
        o = Opinion(type=type,
                    url=random.choice(URLS),
                    locale=random.choice(settings.INPUT_LANGUAGES),
                    user_agent=random.choice(UA_STRINGS[product]))

        if type != input.OPINION_RATING.id:
            o.description = sample()

        if 'mobile':
            manufacturer = random.choice(DEVICES.keys())
            o.manufacturer = manufacturer
            o.device = random.choice(DEVICES[manufacturer])

        o.save(terms=False)

        if type == input.OPINION_RATING.id:
            for question in input.RATING_USAGE:
                Rating(
                    opinion=o,
                    type=question.id,
                    value=random.randint(1, 5)).save()
        o.created = datetime.datetime.now() - datetime.timedelta(
                seconds=random.randint(0, 30 * 24 * 3600))
        o.save()
