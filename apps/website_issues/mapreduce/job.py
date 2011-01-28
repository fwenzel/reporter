import dumbo
from dumbo.lib import identitymapper, identityreducer

# Prepare the job environment. This is like manage.py, but for dumbo jobs.
# The PYTHONPATH for the app needs to be set in the environment.
try: 
    try: import settings_local as settings
    except ImportError: import settings
except ImportError:
    import sys
    sys.stderr.write("Dumbo job cannot find settings. Is the path OK?\n")
    sys.stderr.write("PYTHONPATH: %r" % sys.path)
    sys.exit(1)
from django.core.management import setup_environ
setup_environ(settings)

from website_issues.mapreduce import tasks


"""Dumbo job that can be executed on a hadoop cluster."""


def runner(job):
    job.additer(tasks.SiteSummaryMapper, tasks.CommentClusteringReducer)
    job.additer(identitymapper, tasks.ClusterIdReducer)
    job.additer(identitymapper, tasks.SummarySizeReducer)
    job.additer(identitymapper, tasks.SummaryIdReducer)
    job.additer(identitymapper, tasks.DenormalizingReducer)
    job.additer(identitymapper, identityreducer)

if __name__ == "__main__":
    dumbo.main(runner)
