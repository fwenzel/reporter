# TODO(davedash): liberate from zamboni

import subprocess

from django.conf import settings

call = lambda x: subprocess.Popen(x, stdout=subprocess.PIPE).communicate()


def reindex(rotate=False):
    """
    Reindexes sphinx.  Note this is only to be used in dev and test
    environments.
    """
    calls = [settings.SPHINX_INDEXER, '--all', '--config',
             settings.SPHINX_CONFIG_PATH]

    if rotate:  # pragma: no cover
        calls.append('--rotate')

    print call(calls)[0]


def start_sphinx():
    """
    Starts sphinx.  Note this is only to be used in dev and test environments.
    """

    print call([settings.SPHINX_SEARCHD, '--config',
                settings.SPHINX_CONFIG_PATH])[0]


def stop_sphinx():
    """
    Stops sphinx.  Note this is only to be used in dev and test environments.
    """

    print call([settings.SPHINX_SEARCHD, '--stop', '--config',
                settings.SPHINX_CONFIG_PATH])[0]
