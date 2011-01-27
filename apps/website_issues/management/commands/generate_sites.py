import os, os.path, sys, subprocess, pipes
import bz2
from shutil import rmtree
from optparse import make_option
from tempfile import mkdtemp

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from dumbo.util import system
from website_issues.mapreduce.normalize_to_tsv import normalize_unix

from settings import path


def system(args, more_env={}, stdout=sys.stdout, stderr=sys.stderr):
    print >> stderr, 'Calling:', " ".join(args)
    env = os.environ.copy()
    env.update(more_env)
    process = subprocess.Popen(" ".join(args), shell=True,
                               env=env,
                               stdout=stdout, stderr=stderr)
    return os.waitpid(process.pid, 0)[1] / 256

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
                    dest='do_clean',
                    default=False,
                    help='Clean work/output files and exit.'),
    )

    def handle(self, *args, **options):
        dest_dir = os.path.join(settings.TSV_EXPORT_DIR, "sites")
        if not os.path.exists(dest_dir):
            os.mkdir(dest_dir)
        if options["do_clean"]:
            print "Removing output at %s" % dest_dir
            rmtree(dest_dir)
            return
        print "Using work/output directory: %s" % dest_dir

        source = options['source']
        if source is None:
            source = os.path.join(settings.TSV_EXPORT_DIR, 'opinions.tsv.bz2')
        if not os.path.exists(source):
            raise CommandError("Missing input file: %s" % source)
        if source.endswith(".bz2"):
            print "Decompressing %s" % source
            # we need to decompress the file to disk for dumbo to work with it
            infile = bz2.BZ2File(source)
            outname = os.path.join(dest_dir,
                                   os.path.basename(source[:-len(".bz2")]))
            with open(outname, "w+") as outfile:
                for line in infile: outfile.write(line)
            infile.close()
            source = outname

        mapreduce_dir = path("apps/website_issues/mapreduce")

        dumbo_job_file = os.path.join(mapreduce_dir, "job.py")
        show_counters = os.path.join(mapreduce_dir, "show_counters.py")

        if dest_dir is None: dest_dir = mkdtemp()
        dest = os.path.join(dest_dir, "clustered_comments.tsv.coded")
        if os.path.exists(dest): os.remove(dest)

        print "Generating site from %s using dumbo (unix backend)." % source

        q = lambda s: pipes.quote(s)
        python_env = {"PYTHONPATH": q(":".join(sys.path))}
        system(["dumbo start", q(dumbo_job_file),
                "-input", q(source), "-output", q(dest),
                "2>&1 | python", q(show_counters)],
               more_env=python_env)

        print "Exporting result to %s" % dest_dir
        normalize_unix(open(dest, "r"), dest_dir)

        if options["skip_load"]: return

        print "Loading results into sites database."
        sql_load = os.path.join(mapreduce_dir, "load.sql")
        sql_filter = """sed "s/INFILE '/INFILE '%s\\//g" """ % \
                     q(dest_dir).replace('/', '\\/')
        system(["cat", q(sql_load),
                "|" , sql_filter,
                "| python ./manage.py dbshell --database=website_issues"],
               more_env=python_env)
        normalize_unix(open(dest, "r"), dest_dir)
