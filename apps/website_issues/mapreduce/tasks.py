from itertools import product as cartesian

from textcluster.cluster import Corpus

from website_issues.utils import normalize_url

from input import OPINION_PRAISE, OPINION_ISSUE, OPINION_BROKEN

"""Map/Reduce clustering for sites.

Streaming works in a denormalized fashion, but data is associated to either
a sitesummary (s_*), a cluster (c_*) or a comment (c_*).
"""

# Max site summary and cluster size. Used for lexicographix sorting.
MAX_SIZE = 10**9


def recombined(data):
    """Recombine potentially multiline records single values."""
    parts = []
    for key, value in data:
        if value.endswith('\\'):
            try: value.decode("string_escape")
            except ValueError:
                # the trailing backslash is not escaped -- wait for next line
                parts.append(value[:-1])
                continue
        if len(parts) > 0:
            value = "\n".join(parts)
            parts = []
        yield (key, value)


class SiteSummaryMapper(object):
    """Map each site summary to the matching messages.
    Run n mappers.

    > ((byte,), (m_id, ts, type, product, version, os, locale, manufacturer,
                                                        device, url, message))*
    < ((version, site, os/app, type), (ts, m_id, message))*
    """

    def __init__(self):
        self.comments_in = self.counters["comments in"]
        self.comments_out = self.counters["comments used"]

    def __call__(self, data):
        supported_types = set([OPINION_BROKEN.short,
                               OPINION_ISSUE.short,
                               OPINION_PRAISE.short])
        for key, value in recombined(data):
            self.comments_in += 1
            m_id, ts, type, product, version, os, locale, \
                manufacturer, device, url, message = value.split('\t', 10)
            if not url or type not in supported_types: continue
            app = '<%s>' % product
            site = normalize_url(url)
            out_keys = cartesian((version,), (site,), (app, os, None), (type,))
            out_value = (m_id, message)
            self.comments_out += 1
            for out_key in out_keys: yield (out_key, out_value)


class CommentClusteringReducer(object):
    """Cluster messages for the same site summary.
    Run n reducers (4+ recommended).

    > (version, site, os, type), (m_id, message)+
    < ((sortkey, version, site, os, s_type, c_index, c_type, c_size),
                                                       (m_id, message, score))*
    """
    def __init__(self):
        self.cluster_count = self.counters["clusters"]

    def __call__(self, key, values_gen):
        values = list(values_gen)
        version, site, os, type = key

        def result(s_type, c_index, c_size, m_id, message, score):
            sortkey = MAX_SIZE - c_size
            self.cluster_count += 1
            return \
                (sortkey, version, site, os, s_type, c_index, type, c_size), \
                (m_id, message, score)

        c_index = 1
        if len(values) == 1:
            m_id, message = values[0]
            for s_type in (type, None):
                yield result(s_type, c_index, 1, m_id, message, 1.0)
        else:
            corpus = Corpus()
            unclustered_opinions = {}
            for m_id, message in values:
                unclustered_opinions[m_id] = (m_id, message)
                corpus.add((m_id, message), str=message, key=m_id)

            clusters = corpus.cluster()
            for c in clusters:
                c_index += 1
                rest = [(s["object"], s["similarity"]) for s in c.similars]
                c_size = len(rest) + 1
                for (m_id, message), score in [(c.primary, 1.0)] + rest:
                    del unclustered_opinions[m_id]
                    for s_type in (type, None):
                        yield result(s_type, c_index, c_size, m_id, message,
                                                                         score)

            for m_id, message in unclustered_opinions.values():
                c_index += 1
                for s_type in (type, None):
                    yield result(s_type, c_index, 1, m_id, message, 1.0)


class ClusterIdReducer(object):
    """Assign ids to comments and clusters (for normalization).
    Run only 1 task at a time!

    > (sortkey, version, site, os, s_type, c_index, c_type, c_size),
                                                        (m_id, message, score)+
    < ((version, site, os, s_type),
                        (c_id, c_type, c_size, m_refid, m_id, message, score))*
    """
    def __init__(self):
        self.c_id = 0
        self.m_refid = 0

    def __call__(self, key, values):
        self.c_id += 1
        _, version, site, os, s_type, _, c_type, c_size = key
        for m_id, message, score in values:
            self.m_refid += 1
            yield \
                (version, site, os, s_type), \
                (self.c_id, c_type, c_size, self.m_refid, m_id, message, score)


class SummarySizeReducer(object):
    """Count comments for summary, regardless of cluster type.

    > (version, site, os, s_type),
                         (c_id, c_type, c_size, m_refid, m_id, message, score)+

    < ((sortkey, version, site, os, type),
                (s_size, c_id, c_type, c_size, m_refid, m_id, message, score))*
    """
    def __init__(self):
        self.summaries_count = self.counters["site summaries"]

    def __call__(self, key, values_gen):
        values = list(values_gen)
        s_size = len(values)
        key = ("%09d" % (MAX_SIZE - s_size),) + key
        for value in values:
            yield key, (s_size,) + value
        self.summaries_count += 1


class SummaryIdReducer(object):
    """Assign ids to site summaries (for normalization).
    Also calculates summary size.
    Run only 1 task at a time!

    > (sortkey, version, site, os, type),
                 (s_size, c_id, c_type, c_size, m_refid, m_id, message, score)+

    < ((version, site, os),
            (type, s_id, s_size, c_id, c_size, m_refid, m_id, message, score))*
    """
    def __init__(self):
        self.s_id = 0

    def __call__(self, key, values):
        self.s_id += 1
        _, version, site, os, type = key
        for s_size, c_id, c_type, c_size, m_refid, m_id, message, \
                                                               score in values:
            yield (version, site, os), \
                  (type, self.s_id, s_size, c_id, c_type, c_size, m_refid,
                                                          m_id, message, score)


class DenormalizingReducer(object):
    """Assign ids to site summaries (for normalization).
    Calculate the happy/sad/total counts that need to be displayed for any
    site summary, by peeking at the summaries for the other types.

    Generates the complete denormalize table layout, with the most busy site
    summaries are on top.

    > (version, site, os),
             (type, s_id, s_size, c_id, c_size, m_refid, m_id, message, score)+

    < ((s_id, c_id),
        (version, site, os, type, s_id, s_size, s_sad_size, s_happy_size,
                                 c_id, c_size, m_refid, m_id, message, score))*
    """
    def __call__(self, key, values_gen):
        version, site, os = key
        values = list(values_gen)
        s_sad_size, s_happy_size = 0, 0
        for type, _, s_size, _, _, _, _, _, _, _ in values:
            if type == OPINION_PRAISE.short: s_happy_size = s_size
            else: s_sad_size = s_size
        for type, s_id, s_size, c_id, c_type, c_size, m_refid, m_id, message, \
                                                               score in values:
            yield \
                ("%09d" % s_id, "%09d" % c_id, "%02.5f" % (10.0-score)), \
                (version, site, os, type, s_id,
                 s_size, s_sad_size, s_happy_size,
                 c_id, c_type, c_size,
                 m_refid, m_id, message, score)

