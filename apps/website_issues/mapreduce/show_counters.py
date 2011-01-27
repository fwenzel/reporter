#! /usr/bin/env python

"""Helper tool. Pipe (unix) dumbo jobs in here to get neat counters."""

import re
from sys import argv, stdin, stdout, stderr


THRESHOLD = 10000
MATCHER = re.compile(r"^reporter:counter:[^,]*,(.*),([0-9]+)$")
def main(arguments):
    counters = {}
    thresholds = {}
    for line in stdin:
        match = MATCHER.match(line)
        if match is None:
            stderr.write(line)
            continue
        key, inc = match.groups()
        if key not in counters:
            counters[key] = 0
            thresholds[key] = 0
        counters[key] += int(inc)
        thresholds[key] += int(inc)
        if thresholds[key] >= THRESHOLD:
            thresholds[key] -= THRESHOLD
            out = ["%s=% 8i" % (key, value) for key, value in counters.items()]
            stdout.write("%s \n" % ", ".join(out))
            stdout.flush()
    stdout.write("%r \n" % counters)

if __name__ == "__main__":
    main(argv)
