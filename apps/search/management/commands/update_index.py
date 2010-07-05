from optparse import make_option

from django.core.management.base import NoArgsCommand

from search.utils import reindex


class Command(NoArgsCommand):
    help = reindex.__doc__.strip()
    option_list = NoArgsCommand.option_list + (
        make_option('-r', '--rotate', action='store_true', dest='rotate',
        default=False, help='Rotate indexes.'),
    )

    def handle_noargs(self, **options):
        reindex(options['rotate'])
