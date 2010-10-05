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


def cached_property(*args, **kw):
    # Handles invocation as a direct decorator or
    # with intermediate keyword arguments.
    if args: # @cached_property
        return CachedProperty(args[0])
    else: # @cached_property(name=..., writable=...)
        return lambda f: CachedProperty(f, **kw)


class CachedProperty(object):
    """A decorator that converts a function into a lazy property. The
function wrapped is called the first time to retrieve the result
and than that calculated result is used the next time you access
the value::

class Foo(object):

@cached_property
def foo(self):
# calculate something important here
return 42

Lifted from werkzeug.
"""

    def __init__(self, func, name=None, doc=None, writable=False):
        self.func = func
        self.writable = writable
        self.__name__ = name or func.__name__
        self.__doc__ = doc or func.__doc__

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        _missing = object()
        value = obj.__dict__.get(self.__name__, _missing)
        if value is _missing:
            value = self.func(obj)
            obj.__dict__[self.__name__] = value
        return value

    def __set__(self, obj, value):
        if not self.writable:
            raise TypeError('read only attribute')
        obj.__dict__[self.__name__] = value
