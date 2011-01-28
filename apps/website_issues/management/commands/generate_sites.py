from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from website_issues.mapreduce import generate_sites


class Command(BaseCommand):
    """
    Build clusters per (site x version x os) from opinions read from a database
    export.  A (normalized) 'site' is a set of all urls with the same
    "normalized" form:

    http://xm.pl/search/x, http://www.exam.pl/ -> http://xm.pl
    https://xm.pl/mail, https://exam.pl/mail   -> https://xm.pl
    https://mail.xm.pl, https://mail.xm.pl/y   -> https://mail.xm.pl
    """

    option_list = BaseCommand.option_list + (
        make_option('--source',
                    action='store',
                    dest='source',
                    default=None,
                    help='Custom opinions.tsv (*.bz2 will be decompressed).'),
        make_option('--skip-load',
                    action='store_true',
                    dest='skip_load',
                    default=False,
                    help='Do not load results into the sites database.'),
        make_option('--clean',
                    action='store_true',
                    dest='only_clean',
                    default=False,
                    help='Clean work/output files and exit.'),
    )

    def handle(self, *args, **options):
        return generate_sites(options["source"], 
                              options["skip_load"], 
                              options["only_clean"])
