"""
(Incomplete) bad words list, not to filter every conceivable swear word but
to encourage constructive feedback.
"""
import os
import re


root = os.path.dirname(os.path.realpath(__file__))

WORDLIST = set(
    open(os.path.join(root, 'badwords.txt'), 'r').read().splitlines())
BADWORD_RE = re.compile(r'(?:[^\w]|^)(%s)(?:[^\w]|$)' % (
    '|'.join([ r for r in [ '\w*'.join(map(re.escape, w.split('*'))) for
                            w in WORDLIST ] ])))

def find_swearwords(str):
    """Find swearwords in a string."""
    return BADWORD_RE.findall(str.lower())
