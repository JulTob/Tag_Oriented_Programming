"""Temporary status-only check that -k selects the same tests in order."""

import unittest


def flatten(suite):
    for member in suite:
        if isinstance(member, unittest.TestSuite):
            yield from flatten(member)
        else:
            yield member


base = [case.id() for case in flatten(unittest.TestLoader().discover("tests", top_level_dir="."))]
filtered_loader = unittest.TestLoader()
filtered_loader.testNamePatterns = base
selected = [case.id() for case in flatten(filtered_loader.discover("tests", top_level_dir="."))]
raise SystemExit(0 if selected == base else 1)
