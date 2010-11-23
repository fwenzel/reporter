import urlparse as urlparse_


class ParseResult(urlparse_.ParseResult):
    def geturl(self):
        """Reassemble parsed URL."""
        if self.scheme == 'about':
            return '%s:%s' % (self.scheme, self.netloc)
        else:
            return super(ParseResult, self).geturl()


def urlparse(url):
    """about: and chrome:// URL aware URL parser."""
    if url.startswith('about:'):
        parsed = url.split(':', 1)
        return ParseResult(
            scheme=parsed[0], netloc=parsed[1], path=None, params=None,
            query=None, fragment=None)
    elif url.startswith('chrome://'):
        parsed = url.split('://', 1)[1].split('/')
        path = parsed[1] if len(parsed) > 1 else ''
        return ParseResult(
            scheme='chrome', netloc=parsed[0], path=path,
            params=None, query=None, fragment=None)
    else:
        return urlparse_.urlparse(url)
