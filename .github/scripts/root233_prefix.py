"""Temporary CI diagnosis: return only the success of a test prefix."""

import os
import sys
import unittest


def flatten(suite):
    for member in suite:
        if isinstance(member, unittest.TestSuite):
            yield from flatten(member)
        else:
            yield member


cases = list(flatten(unittest.defaultTestLoader.discover("tests", top_level_dir=".")))
prefix = int(sys.argv[1])
with open(os.devnull, "w") as sink:
    result = unittest.TextTestRunner(stream=sink).run(
        unittest.TestSuite(cases[:prefix])
    )
raise SystemExit(0 if result.wasSuccessful() else 1)
