import zlib


def uniquifier(seq, key=None):
    """
    Make a unique list from a sequence. Optional key argument is a callable
    that transforms an item to its key.

    Borrowed in part from http://www.peterbe.com/plog/uniqifiers-benchmark
    """
    if key is None:
        key = lambda x: x
    def finder(seq):
        seen = {}
        for item in seq:
            marker = key(item)
            if marker not in seen:
                seen[marker] = True
                yield item
    return list(finder(seq))


# TODO(davedash): liberate this
def manual_order(qs, pks, pk_name='id'):
    """
    Given a query set and a list of primary keys, return a set of objects from
    the query set in that exact order.
    """

    if not pks:
        return qs.none()

    objects = qs.filter(id__in=pks).extra(
            select={'_manual': 'FIELD(%s, %s)'
                % (pk_name, ','.join(map(str, pks)))},
            order_by=['_manual'])

    return objects


crc32 = lambda x: zlib.crc32(x) & 0xffffffff
