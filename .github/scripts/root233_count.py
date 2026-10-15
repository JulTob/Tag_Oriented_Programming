"""Temporary status-only check of the test count on the CI interpreter."""

import sys
import unittest


def flatten(suite):
    for member in suite:
        if isinstance(member, unittest.TestSuite):
            yield from flatten(member)
        else:
            yield member


count = sum(1 for _ in flatten(unittest.defaultTestLoader.discover("tests", top_level_dir=".")))
raise SystemExit(0 if count == int(sys.argv[1]) else 1)
