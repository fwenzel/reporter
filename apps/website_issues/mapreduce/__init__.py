import os, os.path, sys, subprocess, pipes
import bz2
from shutil import rmtree
from tempfile import mkdtemp

from dumbo.util import system

from django.conf import settings
from settings import path

from website_issues.mapreduce.normalize_to_tsv import normalize_unix

def _system(args, more_env={}):
    print >> sys.stderr, 'Calling:', " ".join(args)
    env = os.environ.copy()
    env.update(more_env)
    process = subprocess.Popen(" ".join(args), shell=True,
                               env=env,
                               stdout=sys.stdout,
                               stderr=sys.stderr)
    exit_code = os.waitpid(process.pid, 0)[1] & 0xff
    if 0 != exit_code:
        raise Exception("System call '%s' failed!" % " ".join(args))


def generate_sites(source, skip_load=False, only_clean=False):
    dest_dir = mkdtemp()
    if only_clean:
        print "Removing output at %s" % dest_dir
        rmtree(dest_dir)
        return
    print "Using work/output directory: %s" % dest_dir

    if source is None:
        source = os.path.join(settings.TSV_EXPORT_DIR, 'opinions.tsv.bz2')
    if not os.path.exists(source):
        raise Exception("Missing input file: %s" % source)
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

    dest = os.path.join(dest_dir, "clustered_comments.tsv.coded")
    if os.path.exists(dest): os.remove(dest)

    print "Generating site from %s using dumbo (unix backend)." % source

    q = lambda s: pipes.quote(s)
    python_env = {"PYTHONPATH": q(":".join(sys.path))}
    _system(["dumbo start", q(dumbo_job_file),
             "-input", q(source), "-output", q(dest),
             "2>&1 | python", q(show_counters)],
            more_env=python_env)

    print "Exporting result to %s" % dest_dir
    normalize_unix(open(dest, "r"), dest_dir)
    if skip_load: return

    print "Loading results into sites database."
    sql_load = os.path.join(mapreduce_dir, "load.sql")
    sql_filter = """sed "s/INFILE '/INFILE '%s\\//g" """ % \
                 q(dest_dir).replace('/', '\\/')
    _system(["cat", q(sql_load),
             "|" , sql_filter,
             "| python ./manage.py dbshell --database=website_issues"],
            more_env=python_env)
    normalize_unix(open(dest, "r"), dest_dir)
