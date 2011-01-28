"""Version comparison module for Mozilla-style application versions."""
# TODO liberate

import re

from django.utils.functional import memoize

from input.utils import uniquifier


version_re = re.compile(r"""(?P<major>\d+)      # major (x in x.y)
                            \.(?P<minor1>\d+)   # minor1 (y in x.y)
                            \.?(?P<minor2>\d+)? # minor2 (z in x.y.z)
                            \.?(?P<minor3>\d+)? # minor3 (w in x.y.z.w)
                            (?P<alpha>[a|b]?)   # alpha/beta
                            (?P<alpha_ver>\d*)  # alpha/beta version
                            (?P<pre>pre)?       # pre release
                            (?P<pre_ver>\d)?    # pre release version""",
                        re.VERBOSE)


class Version(object):
    """An object representing a version."""
    _version = None
    _version_int = None
    _version_dict = None

    def __init__(self, version):
        """Version constructor."""
        try:
            # Parse version.
            assert version
            self._version = version
            self._version_int = version_int(version)
            assert version_int != 0
            self._version_dict = version_dict(version)

            # Make parsed data available as properties.
            for key, val in self._version_dict.items():
                setattr(self, key, val)

        except AssertionError, e:
            raise ValueError('Error parsing version: %s' % e)

    def __cmp__(self, other):
        """Compare two versions."""
        assert isinstance(other, Version)
        return cmp(self._version_int, other._version_int)

    @property
    def is_beta(self):
        """
        Is this a beta version?

        Nightlies, while containing "b2" etc., are not betas.
        """
        return self.alpha == 'b' and not self.is_nightly

    @property
    def is_nightly(self):
        return self.pre == 'pre'

    @property
    def is_release(self):
        return not (self.is_beta or self.is_nightly)

    @property
    def simplified(self):
        return simplify_version(self._version)


def dict_from_int(version_int):
    """Converts a version integer into a dictionary with major/minor/...
    info."""
    d = {}
    rem = version_int
    (rem, d['pre_ver']) = divmod(rem, 100)
    (rem, d['pre']) = divmod(rem, 10)
    (rem, d['alpha_ver']) = divmod(rem, 100)
    (rem, d['alpha']) = divmod(rem, 10)
    (rem, d['minor3']) = divmod(rem, 100)
    (rem, d['minor2']) = divmod(rem, 100)
    (rem, d['minor1']) = divmod(rem, 100)
    (rem, d['major']) = divmod(rem, 100)
    d['pre'] = None if d['pre'] else 'pre'
    d['alpha'] = {0: 'a', 1: 'b'}.get(d['alpha'])

    return d


def version_dict(version):
    """Turn a version string into a dict with major/minor/... info."""
    match = version_re.match(version or '')
    letters = 'alpha pre'.split()
    numbers = 'major minor1 minor2 minor3 alpha_ver pre_ver'.split()
    if match:
        d = match.groupdict()
        for letter in letters:
            d[letter] = d[letter] if d[letter] else None
        for num in numbers:
            d[num] = int(d[num]) if d[num] else None
    else:
        d = dict((k, None) for k in numbers)
        d.update((k, None) for k in letters)
    return d
_version_dict_cache = {}
version_dict = memoize(version_dict, _version_dict_cache, 1)


def version_int(version):
    version_data = version_dict(str(version))

    d = {}
    for key in ['alpha_ver', 'major', 'minor1', 'minor2', 'minor3',
                'pre_ver']:
        d[key] = version_data.get(key) or 0
    atrans = {'a': 0, 'b': 1}
    d['alpha'] = atrans.get(version_data['alpha'], 2)
    d['pre'] = 0 if version_data['pre'] else 1

    v = "%d%02d%02d%02d%d%02d%d%02d" % (d['major'], d['minor1'],
            d['minor2'], d['minor3'], d['alpha'], d['alpha_ver'], d['pre'],
            d['pre_ver'])
    return int(v)
_version_int_cache = {}
version_int = memoize(version_int, _version_int_cache, 1)


def simplify_version(version):
    """
    Strips cruft (like build1, which won't show up in a UA string) from a
    version number by parsing and rebuilding it.
    """
    v = dict_from_int(version_int(version))
    # major and minor1 always exist
    pieces = [v['major'], v['minor1']]
    suffixes = []

    # minors 2 and 3 are optional
    if v['minor2']:
        pieces.append(v['minor2'])
    if v['minor3']:
        pieces.append(v['minor3'])

    # if this is a real beta, attach the version
    if v['alpha'] and v['alpha_ver']:
        suffixes += [v['alpha'], v['alpha_ver']]

    # attach pre
    if v['pre'] and v['alpha_ver']:
        suffixes.append(v['pre'])
        if v['pre_ver']:
            suffixes.append(v['pre_ver'])

    # stringify
    pieces = map(str, pieces)
    suffixes = map(str, suffixes)

    # build version number
    return '.'.join(pieces) + ''.join(suffixes)


def version_list(releases, key=None, reverse=True, hide_below='0.0'):
    """
    Build a sorted list of simplified versions.

    ``releases`` is expected to be a dictionary like:
        {'1.0': '2000-01-01'}
    """
    if not key:
        key = lambda x: x[1]  # Default: Sort by release date.

    lowest = Version(hide_below)
    versions = []
    for v, released in sorted(releases.items(), key=key, reverse=reverse):
        ver = Version(v)
        if ver < lowest:
            continue
        versions.append(ver.simplified)
    return uniquifier(versions)
