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


def normalize_url(url):
    """Strips paths (and any "www." host) from a given URL.

    Keeps the protocol and non-www hosts/subdomains.

    >>> normalize_url('http://google.com/test')
    'http://google.com'
    >>> normalize_url('http://www.google.com:8080/')
    'http://google.com:8080'
    >>> normalize_url('about:config')
    'about:config'
    >>> normalize_url('https://mail.example.co.uk/.www/://?argl=#pff')
    'https://mailexample.co.uk'
    >>> normalize_url('https://user:pass@www.example.co.uk/')
    'https://mailexample.co.uk'
    """
    parse_result = urlparse(url)
    if parse_result.scheme == 'about':
        return parse_result.geturl()
    netloc = parse_result.netloc
    if netloc.startswith("www."): netloc = netloc[4:]
    return ''.join((parse_result.scheme, '://', netloc))
