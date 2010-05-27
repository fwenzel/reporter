from hashlib import sha256

from django.core.cache import cache


def cached(ctime=3600):
    """
    Per-function caching decorator.
    http://djangosnippets.org/snippets/1852/
    """
    def decr(func):
        def wrp(*args,**kargs):
            key = sha256(func.func_name+repr(args)+repr(kargs)).hexdigest()
            res = cache.get(key)
            if res is None:
                res = func(*args,**kargs)
                cache.set(key,res,ctime)
            return res
        return wrp
    return decr
