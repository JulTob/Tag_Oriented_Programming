"""Temporary diagnosis: run a prefix through the standard unittest CLI."""

import os
import subprocess
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
command = [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-t", "."]
for case in cases[:prefix]:
    command.extend(("-k", case.id()))

with open(os.devnull, "w") as sink:
    result = subprocess.run(command, stdout=sink, stderr=sink, check=False)
raise SystemExit(result.returncode)
