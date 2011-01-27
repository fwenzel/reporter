#! /usr/bin/env python

import os.path
import csv
from sys import argv, exit, stderr, stdin

from dumbo.util import loadcode

from api.cron import TSVDialect


def writer(outfile):
    return csv.writer(outfile, TSVDialect)

def _put(writer, row):
    writer.writerow([v for v in row])

def positive(type):
    if type is None: return "NULL"
    return 1 if type == "praise" else 0

def maybe_os(os):
    return "NULL" if os is None else os

def normalize_to_tsv(source, sitesummaries, clusters, comments):
    """Converts python-repr-coded objects (emitted by our reducers) back into
       mysql-tsv compatible output.

       code_in is a standard file-like object to read from
       comments, clusters and sitesummaries are csv.writer-compatible objects

       The input column order is the one defined by the DenormalizingReducer:
       > (version, site, os, type, s_id, s_size, s_sad_size, s_happy_size,
                           c_id, c_type, c_size, m_refid, m_id, message, score)

        The output column order corresponds to the table column order (see
        website_issues/model.py)
    """

    last_s_id = -1
    last_c_id = -1
    for key, value in source:
        version, site, os, type, s_id, s_size, s_sad_size, s_happy_size, \
            c_id, c_type, c_size, m_refid, m_id, message, score = value
        if c_id != last_c_id:
            if s_id != last_s_id:
                last_s_id = s_id
                _put(sitesummaries, [s_id, site, version, positive(type),
                                     maybe_os(os), s_size, s_sad_size,
                                     s_happy_size])
            last_c_id = c_id
            _put(clusters, [c_id, s_id, c_size, message, m_refid,
                            positive(c_type)])
        _put(comments, [m_refid, c_id, message, m_id, score])


def _normalize(source, dest_dir):
    names = ("sitesummaries.tsv", "clusters.tsv", "comments.tsv")
    files = [open(os.path.join(dest_dir, name), "w+") for name in names]
    normalize_to_tsv(source, *[writer(f) for f in files])

def normalize_unix(source, dest_dir):
    return _normalize(loadcode(source), dest_dir)

def main(arguments):
    if len(arguments) != 2 or not os.path.exists(arguments[1]):
        usage = "Usage: %s DEST_DIR\n\n" \
            "Denormalized mapred output is read from STDIN.\n" \
            "Output is written to three files in the given directory:\n" \
            "    sitesummaries.tsv clusters.tsv comments.tsv\n" \
            "The destination directory mus exist.\n" \
            "If the output files exist, they are overwritten.\n"
        stderr.write(usage % arguments[0])
        return 1

    normalize_unix(sys.stdin, arguments[1])
    return 0


if __name__ == "__main__":
    exit(main(argv))
