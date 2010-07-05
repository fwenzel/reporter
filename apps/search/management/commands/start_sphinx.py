from django.core.management.base import NoArgsCommand

from search.utils import start_sphinx


class Command(NoArgsCommand):
    help = start_sphinx.__doc__.strip()

    def handle_noargs(self, **options):
        start_sphinx()
