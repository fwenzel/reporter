import dumbo
from dumbo.lib import identitymapper, identityreducer

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
