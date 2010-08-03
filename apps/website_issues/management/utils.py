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
    # urlparse lib does not play nicely with about: urls
    if url.find('/') == -1: return url
    protocol_end = url.find("://") + 3
    # do not touch something like about:config
    if protocol_end == -1 + 3: return url
    protocol = url[:protocol_end]
    host = url[protocol_end : url.find('/', protocol_end)]
    login_end = host.find('@')
    if login_end != -1:
        host = host[login_end+1:]
    if host.startswith("www."): host = host[4:]
    return ''.join([protocol, host])
