from django.core.management.base import NoArgsCommand

from search.utils import stop_sphinx


class Command(NoArgsCommand):
    help = stop_sphinx.__doc__.strip()

    def handle_noargs(self, **options):
        stop_sphinx()
