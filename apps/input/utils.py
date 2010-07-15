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
