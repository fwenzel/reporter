import datetime
import random

from django.conf import settings
from django.db import transaction

import cronjobs

import feedback
from feedback.models import Opinion

DEFAULT_NUM_OPINIONS = 100
TYPES = list(feedback.OPINION_TYPES)
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
UA_STRINGS = ['Mozilla/5.0 (Android; Linux armv71; rv:2.0b6pre) Gecko/'
              '20100924 Namoroka/4.0b7pre Fennec/2.0b1pre']
DEVICES = dict(Samsung = 'Epic Vibrant Transform'.split(),
               HTC = 'Evo Hero'.split(),
               Motorola = 'DroidX Droid2'.split())

# TODO: More than just Fennec.
@cronjobs.register
@transaction.commit_on_success
def populate():
    num_opinions = getattr(settings, 'NUM_FAKE_OPINIONS', DEFAULT_NUM_OPINIONS)

    for i in xrange(num_opinions):
        print "Creating %d of %d opinions" % (i, num_opinions)
        manufacturer = random.choice(DEVICES.keys())
        device = random.choice(DEVICES[manufacturer])
        o = Opinion.objects.create(type=random.choice(TYPES),
                                   url=random.choice(URLS),
                                   description=sample(),
                                   user_agent=random.choice(UA_STRINGS),
                                   manufacturer=manufacturer,
                                   device=device)
        o.created = datetime.datetime.now() - datetime.timedelta(
                seconds=random.randint(0, 30 * 24 * 3600))
        o.save()
