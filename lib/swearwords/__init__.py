"""
(Incomplete) bad words list, not to filter every conceivable swear word but
to encourage constructive feedback.
"""
import os


root = os.path.dirname(os.path.realpath(__file__))

WORDLIST = set(
    open(os.path.join(root, 'badwords.txt'), 'r').read().splitlines())
